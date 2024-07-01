import sys
import copy
sys.path.append("../helper")
from helper.utils import *
from models.event import Event
from models.transaction import Transaction
from models.block import Block
from models.blockchain import BlockChain
import json
import random
import networkx as nx

script_dir = os.path.dirname(os.path.abspath(__file__))
params_path = os.path.join(script_dir, "../helper", "params.json")

class SelfishNode:
    def __init__(
        self,
        nodeID,
        genesisBlock,
        mineTime,
        lowSpeed=False,
        latencyMatrix=None
    ):
        self.nodeID = nodeID
        self.lowSpeed = lowSpeed
        self.mineTime = mineTime

        self.neighbors = set()
        self.blockchain = BlockChain()
        self.latencyMatrix = latencyMatrix

        # State=None means 0' state
        self.state=0
        self.privateChain=[]

        self.addGenesisBlock(genesisBlock)

    def addGenesisBlock(self, genesisBlock):
        """
        Adds the Genesis Block
        """
        self.blockchain.addGenesisBlock(genesisBlock)

    def calculateLatency(self,peer,size):
        """
        Return latency between two Nodes in seconds\n
        peer (Node): Destination\n
        size: Packet Size in KB\n
        Return: float (seconds)
        """
        if(peer.lowSpeed):
            lowLinkSpeedMbps = json.load(open(params_path))["low-link-speed-Mbps"]
            # Converting to bps
            c = lowLinkSpeedMbps*(10**6)
        else:
            highLinkSpeedMbps = json.load(open(params_path))["high-link-speed-Mbps"]
            # Converting to bps
            c = highLinkSpeedMbps*(10**6)

        queuingDelayMean=json.load(open(params_path))["queuing-delay-mean-Kb"]
        # Converting to Kb to bits
        queuingDelayMean=queuingDelayMean*1000
        d = randomGenerator.exponential(queuingDelayMean/c)
        
        # Convert size KB to bits
        size = size*1000*8

        # Convert propagation speed to sec
        propagationSpeed=self.latencyMatrix[self.nodeID][peer.nodeID]/1000
        transmissionSpeed=size/c

        return propagationSpeed + transmissionSpeed + d

    def getCoinbaseTxn(self):
        """
        Returns a Mining TXN
        """
        # Get new tranasaction ID
        txnID = generateTransactionID()

        # Get the mining value
        miningValue = json.load(open(params_path))["mining-fee"]

        # Prepare the mining TXN and add it to included txn list
        miningTxn = Transaction(
            txnID=txnID,
            senderPeerID=-1,
            receiverPeerID=self.nodeID,
            val=miningValue,
            type=1,
        )
        return miningTxn

    def floodTxn(self, txn, time):
        """
        Broadcast TXN to Neighbours
        """
        for peer in self.neighbors:
            # Calculate Latency
            latency = self.calculateLatency(peer, size=json.load(open(params_path))["transaction-size-KB"])
            # Push flooding event to the event queue
            pushToEventQueue(
                Event(
                    time=time + latency,
                    type=1,
                    txn=txn,
                    senderPeer=self,
                    receiverPeer=peer,
                )
            )

    def floodBlock(self, block: Block, time):
        """
        Broadcast Block to Neighbours
        """
        for peer in self.neighbors:
            # Calculate Latency
            latency = self.calculateLatency(
               peer=peer, size=block.size
            )
            pushToEventQueue(
                Event(
                    time=time + latency,
                    type=4,
                    senderPeer=self,
                    receiverPeer=peer,
                    block=block,
                )
            )

    def checkValidTxnsInBlock(self, block: Block):
        """
        Check if the Transaction 
        inside the BLocks are valid
        """
        # Get the previous block balance
        prevBlock: Block = self.blockchain.rcvdBlocks[block.prevBlockID]
        prevBlockBalance = list(prevBlock.balance)

        # Get the current balance
        currentBalance = list(block.balance)

        # Add/Subtract the transaction from the previous balance
        # Expected to get the current balance
        for txn in block.txnList:
            if txn.type == 1:
                prevBlockBalance[txn.receiverPeerID]+=txn.val
                continue
            prevBlockBalance[txn.receiverPeerID]+=txn.val
            prevBlockBalance[txn.senderPeerID]-=txn.val
        # Check if the current balance is same as expected
        for i in range(len(prevBlockBalance)):
            if prevBlockBalance[i]!=currentBalance[i] or currentBalance[i]<0:
                return False        
        return True

    def validateNormalBlocks(self, block: Block, time):
        """
        Validate Received Block and add it to the chain
        """
        # Add the block to the blockchain
        self.blockchain.rcvdBlocks[block.blockID]=block
        self.blockchain.rcvdBlocksTime[block.blockID]=time

        # Check if blockchain is in received blocks or block parent is an orphan
        if (block.prevBlockID not in self.blockchain.rcvdBlocks) or (block.prevBlockID in self.blockchain.orphanBlocks):
            # print("Node:",self.nodeID,":Orphan Block:",block.blockID,"Received Block Parent:",block.prevBlockID)
            self.blockchain.orphanBlocks.add(block.blockID)
            return
        
        # Check if txns inside the block are valid
        # print(self.nodeID,block.blockID, block.blockID in self.blockchain.rcvdBlocks, self.checkValidTxnsInBlock(block))
        if not self.checkValidTxnsInBlock(block):
            self.blockchain.invalidBlocks.add(block.blockID)
            del self.blockchain.rcvdBlocks[block.blockID]
            return


        # Check if the block is making a longer chain
        if self.blockchain.lastBlock.length<block.length:
            self.updateLongestChain(block)
            event=Event(time=time,type=2,receiverPeer=self)
            pushToEventQueue(event)

        # After adding the block in chain,
        # Process orphan blocks
        self.processOrphanBlocks(time)

    def validateSelfishBlocks(self, block: Block):
        """
        Validate selfishly mined blocks by the node,
        add it to the chain and flood to the N/W
        """

        # Get mining finish time of the block
        time=self.blockchain.rcvdBlocksTime[block.blockID]
        
        # Check if the block is making a longer chain
        if self.blockchain.lastBlock.length<block.length:
            # Update the longest chain
            self.updateLongestChain(block)
        
        # FLood the block to the network
        self.floodBlock(block,time)

    def processOrphanBlocks(self, time):
        """
        Process Blocks which didn't have parent
        """
        # List for storing all orphans
        deleteOrphan=[]
        for blockID in self.blockchain.orphanBlocks:
            block: Block = self.blockchain.rcvdBlocks[blockID]
            # Check if parent of the orphan block is invalid
            if block.prevBlockID in self.blockchain.invalidBlocks:
                # Add the orphan block to invalid block
                self.blockchain.invalidBlocks.add(block.blockID)
                del self.blockchain.rcvdBlocks[block.blockID]
                deleteOrphan.append(block.blockID)
                continue

            # If block is still orphan
            if block.prevBlockID not in self.blockchain.rcvdBlocks or block.prevBlockID in self.blockchain.orphanBlocks:
                continue
            
            # Not an orphan
            # Then orphan is not an orphan now
            deleteOrphan.append(block.blockID)

            # Check the txns if txn is valid
            if not self.checkValidTxnsInBlock(block):
                # Add the block to invalid block
                self.blockchain.invalidBlocks.add(block.blockID)
                del self.blockchain.rcvdBlocks[block.blockID]
                continue
            # Check if it's increasing the length
            if self.blockchain.lastBlock.length<block.length:
                # Update the longest chain
                self.updateLongestChain(block)

                # Start a mining event
                event=Event(time=time,type=2,receiverPeer=self)
                pushToEventQueue(event)

        # Remove the orphan blocks
        for blockID in deleteOrphan:
            self.blockchain.orphanBlocks.remove(blockID)

    def updateLongestChain(self, block: Block):
        """
        Updates longest chain
        """
        self.blockchain.lastBlock=block

    def releaseChain(self):
        # print(self.nodeID,":Releasing Chain:",len(self.privateChain))
        for block in self.privateChain:
            self.validateSelfishBlocks(block)
        self.privateChain=[]

    def eventHandler(self, event):
        """
        Redirects event to 
        required functions
        """
        if event.type == 0:
            self.generateTXN(event)
        elif event.type == 1:
            self.receiveTXN(event)
        elif event.type == 2:
            self.mineBlock(event)
        elif event.type == 3:
            self.finishMine(event)
        elif event.type == 4:
            self.receiveBlock(event)
        else:
            raise ValueError(f"Event Type not Valid")

    # Event - 0
    def generateTXN(self, event: Event):
        """
        Generates a Transaction and propagates to all it's peers
        """
        # Get the last balance of this node
        selfBalance = self.blockchain.lastBlock.balance[event.txn.senderPeerID]
        # Check if the balance satisfying the least condition
        if selfBalance <= 0:
            return
        # Randomly generate a txn value
        event.txn.val = randomGenerator.uniform(0, selfBalance/10+1)
        
        # Add it to received txn
        self.blockchain.rcvdTxns.add(event.txn)
        # Propagate the txn to all it's peers
        self.floodTxn(event.txn,event.time)

    # Event - 1
    def receiveTXN(self, event: Event):
        """
        Receive Transaction Generated by other Peers
        and Propagates to all it's peers
        """
        # Check if the transaction is already received
        if event.txn in self.blockchain.rcvdTxns:
            return
        if self.blockchain.lastBlock.balance[event.txn.senderPeerID]<event.txn.val:
            return
        
        # Add it to received txn
        self.blockchain.rcvdTxns.add(event.txn)

        # Propagate the transaction to it's peers
        self.floodTxn(event.txn, event.time)

    # Event - 2
    def mineBlock(self, event: Event):
        """
        Mines a New Block using a 
        subset of transactions from 
        pending txn pool
        """
        t=event.time

        # Select Last Block according to the state
        if self.state==None or self.state==0:
            lastBlock: Block = self.blockchain.lastBlock
            
        else:
            lastBlock: Block = self.privateChain[-1]

        # Get coinbase txn
        coinbaseTxn = self.getCoinbaseTxn()
        
        # Get the remaining TXN
        txnsAlreadyInChain=set()

        # Traverse from the last block to genesis block
        # to get the set of txn included in the chain
        temp=lastBlock
        while temp.blockID!=1:
            txnsAlreadyInChain=txnsAlreadyInChain.union(lastBlock.txnList)
            temp=self.blockchain.rcvdBlocks[temp.prevBlockID]
        
        # Get the remaining txn by subtracting the txns already in chain
        pendingTxns = self.blockchain.rcvdTxns - txnsAlreadyInChain

        # Get the maximum block size
        blockSize = json.load(open(params_path))["block-size-KB"]

        # Randomly choose number of transaction, but ensure
        # it is does not exceed the blocksize-1
        # Why -1? 1 for the mining TXN
        numOfTxn = len(pendingTxns)
        if numOfTxn > 1:
            numOfTxn = min(random.randint(1, len(pendingTxns)), blockSize - 1)

        # Get the current balance
        currentBalance = list(lastBlock.balance)
        txnToBeIncluded = set()

        # Choose the transaction to be included
        for txn in pendingTxns:
            # Check if the sender has enough balance
            if currentBalance[txn.senderPeerID]-txn.val<0:
                continue
            currentBalance[txn.senderPeerID]-=txn.val
            currentBalance[txn.receiverPeerID]+=txn.val
            txnToBeIncluded.add(txn)
            # Check if we have included enough txn
            if len(txnToBeIncluded)==numOfTxn:
                break

        # Add the coinbase txn
        txnToBeIncluded.add(coinbaseTxn)
        currentBalance[coinbaseTxn.receiverPeerID]+=coinbaseTxn.val

        # Get new block ID
        blockID = generateBlockID()

        # Prepare a block with the transaction chosen
        block = Block(
            blockID=blockID,
            prevBlockID=lastBlock.blockID,
            prevLengthOfChain=lastBlock.length,
            txnList=txnToBeIncluded,
            miner=self,
            prevBlockBalance=list(lastBlock.balance),\
        )
        # Add the latency for the block propagation to it's peers
        t += randomGenerator.exponential(self.mineTime)
        # Add to the event queue with type = 3
        pushToEventQueue(Event(time=t, type=3, block=block, receiverPeer=self))

    # Event - 3
    def finishMine(self, event: Event):
        """
        Finish Mining a Block.
        Propagate it to neighbours.
        Update longest chain if needed
        """
        block: Block=event.block

        # Select Last Block according to the state
        if self.state==None or self.state==0:
            lastBlock: Block = self.blockchain.lastBlock
        else:
            lastBlock: Block = self.privateChain[-1]

        # Check if the longest chain has changed
        if block.prevBlockID!=lastBlock.blockID:
            return
        
        # Add the block to the blockchain
        self.blockchain.rcvdBlocks[block.blockID]=block
        self.blockchain.rcvdBlocksTime[block.blockID]=event.time

        # Add block mined to the private chain
        self.privateChain.append(block)
        
        if self.state==None:
            # If state is 0', 
            # and a selfish block is mined
            # Release the chain
            # and Jump to state 0
            self.state=0
            self.releaseChain()
        else:
            # Otherwise, 
            # increment the state
            self.state+=1

        # Start mining again
        event=Event(time=event.time,type=2,receiverPeer=self)
        pushToEventQueue(event)

    # Event - 4
    def receiveBlock(self, event: Event):
        """
        Receive a Block.
        Validate and Update Chain if needed.
        """
        block = event.block
        # Check if the block is already received
        if block.blockID in self.blockchain.rcvdBlocks:
            return

        # Check state of the Selfish Node
        # Take action based on it
        if self.state==None:
            # If state is 0', 
            # and honest block is received
            # Jump to state 0
            self.state=0
        elif self.state==0:
            # If state is 0, 
            # and honest block is received
            # Stay at state 0
            self.state=0
        elif self.state==1:
            # If state is 1, 
            # and honest block is received
            # Release the chain and Jump to state 0'
            self.state=None
            self.releaseChain()
        elif self.state==2:
            # If state is 2, 
            # and honest block is received
            # Release the chain and Jump to state 0
            self.state=0
            self.releaseChain()
        else:
            # If state is >2, 
            # and honest block is received
            # Release one block from the chain
            # and Jump to state-1
            self.state-=1
            selfishBlock=self.privateChain.pop(0)
            self.validateSelfishBlocks(selfishBlock)
        
        # Validate the received block
        self.validateNormalBlocks(block,event.time)
