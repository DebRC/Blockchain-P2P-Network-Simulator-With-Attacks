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

class Node:
    def __init__(
        self,
        nodeID,
        genesisBlock,
        mineTime,
        lowSpeed=False,
        lowCPU=False,
        latencyMatrix=None
    ):
        self.nodeID = nodeID
        self.lowSpeed = lowSpeed
        self.lowCPU = lowCPU
        self.mineTime = mineTime

        self.neighbors = set()
        self.blockchain = BlockChain()
        self.latencyMatrix = latencyMatrix

        self.g = nx.DiGraph()
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
        if(self.lowSpeed or peer.lowSpeed):
            c = 5
        else:
            c = 100
        d = randomGenerator.exponential(96/c)
        # Convert KB to bits
        size = size*1000*8
        return (self.latencyMatrix[self.nodeID][peer.nodeID] + size/c + d)/1000

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
            # TXN Size KB
            latency = self.calculateLatency(peer, size=1)
            pushToEventQueue(
                Event(
                    time=time + latency,
                    type=1,
                    txn=txn,
                    senderPeer=self,
                    receiverPeer=peer,
                )
            )

    def floodBlock(self, block, time):
        """
        Broadcast Block to Neighbours
        """
        for peer in self.neighbors:
            # Sending block size in KB
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
        prevBlock: Block = self.blockchain.rcvdBlocks[block.prevBlockID]
        prevBlockBalance = list(prevBlock.balance)
        currentBalance = list(block.balance)
        for txn in block.txnList:
            if txn.type == 1:
                prevBlockBalance[txn.receiverPeerID]+=txn.val
                continue
            prevBlockBalance[txn.receiverPeerID]+=txn.val
            prevBlockBalance[txn.senderPeerID]-=txn.val
        for i in range(len(prevBlockBalance)):
            if prevBlockBalance[i]!=currentBalance[i] or currentBalance[i]<0:
                return False        
        return True

    def validateAndForward(self, block: Block, time):
        """
        Validate and forward Block to the N/W
        """
        # Add the block to the blockchain
        self.blockchain.rcvdBlocks[block.blockID]=block
        self.blockchain.rcvdBlocksTime[block.blockID]=time
        self.g.add_edge(block.blockID,block.prevBlockID)

        # Check if blockchain is in received blocks or block parent is an orphan
        if (block.prevBlockID not in self.blockchain.rcvdBlocks) or (block.prevBlockID in self.blockchain.orphanBlocks):
            self.blockchain.orphanBlocks.add(block.blockID)
            return
        
        # Check if txns inside the block are valid
        if not self.checkValidTxnsInBlock(block):
            self.blockchain.invalidBlocks.add(block.blockID)
            del self.blockchain.rcvdBlocks[block.blockID]
            return

        # Check if the block is making a longer chain
        if self.blockchain.lastBlock.length<block.length:
            self.updateLongestChain(block)
            event=Event(time=time,type=2,receiverPeer=self)
            pushToEventQueue(event)
        self.floodBlock(block,time)

        # After adding the block in chain,
        # Process orphan blocks
        self.processOrphanBlocks(time)

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
            # Then orphan is not an orphan
            #  now
            deleteOrphan.append(block.blockID)
            # Check the txns
            if not self.checkValidTxnsInBlock(block):
                self.blockchain.invalidBlocks.add(block.blockID)
                del self.blockchain.rcvdBlocks[block.blockID]
                continue
            # Check if it's increasing the length
            if self.blockchain.lastBlock.length<block.length:
                self.updateLongestChain(block)
                event=Event(time=time,type=2,receiverPeer=self)
                pushToEventQueue(event)
            self.floodBlock(block, time)

        for blockID in deleteOrphan:
            self.blockchain.orphanBlocks.remove(blockID)

    def updateLongestChain(self, block: Block):
        """
        Updates longest chain
        """
        if block.prevBlockID == self.blockchain.lastBlock.blockID:
            for txn in block.txnList:
                if txn.txnID in self.blockchain.pendingTxns:
                    self.blockchain.pendingTxns.remove(txn.txnID)
        else:
            for txnID in self.blockchain.rcvdTxns:
                self.blockchain.pendingTxns.add(txnID)
            temp=copy.deepcopy(block)
            while(True):
                for txn in temp.txnList:
                    if txn.txnID in self.blockchain.pendingTxns:
                        self.blockchain.pendingTxns.remove(txn.txnID)
                if(temp.prevBlockID==0):
                    break
                temp=self.blockchain.rcvdBlocks[temp.prevBlockID]
        self.blockchain.lastBlock=block

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
        self.blockchain.pendingTxns.add(event.txn.txnID)
        self.blockchain.rcvdTxns[event.txn.txnID]=event.txn
        # Propagate the txn to all it's peers
        self.floodTxn(event.txn,event.time)

    # Event - 1
    def receiveTXN(self, event: Event):
        """
        Receive Transaction Generated by other Peers
        and Propagates to all it's peers
        """
        # Check if the transaction is already received
        if event.txn.txnID in self.blockchain.rcvdTxns:
            return
        if self.blockchain.lastBlock.balance[event.txn.senderPeerID]<event.txn.val:
            return
        # Add it to the received TXN
        self.blockchain.pendingTxns.add(event.txn.txnID)
        self.blockchain.rcvdTxns[event.txn.txnID]=event.txn
        # Propagate the transaction to it's peers
        self.floodTxn(event.txn, event.time)

    # Event - 2
    def mineBlock(self, event: Event):
        """
        Mines a New Block using a 
        subset of transactions from 
        pending txn pool
        """
        #
        # print("Event:mineBlock")
        t=event.time
        lastBlock: Block = self.blockchain.lastBlock

        # Get coinbase txn
        coinbaseTxn = self.getCoinbaseTxn()
        
        # Get the remaining TXN
        pendingTxns = self.blockchain.pendingTxns

        numOfTxn = len(pendingTxns)

        # Get the maximum block size
        blockSize = json.load(open(params_path))["block-size"]

        # Randomly choose number of transaction, but ensure
        # it is does not exceed the blocksize-2
        # Why 2? 1 for the block itself and 1 for the mining TXN
        if numOfTxn > 1:
            numOfTxn = min(random.randint(1, len(pendingTxns)), blockSize - 1)

        currentBalance = list(lastBlock.balance)
        txnToBeIncluded = set()

        for txnID in pendingTxns:
            txn: Transaction = self.blockchain.rcvdTxns[txnID]
            if currentBalance[txn.senderPeerID]-txn.val<0:
                continue
            currentBalance[txn.senderPeerID]-=txn.val
            currentBalance[txn.receiverPeerID]+=txn.val
            txnToBeIncluded.add(txn)
            if len(txnToBeIncluded)==blockSize-2:
                break

        txnToBeIncluded.add(coinbaseTxn)

        # Get new block ID
        blockID = generateBlockID()

        currentBalance[coinbaseTxn.receiverPeerID]+=coinbaseTxn.val

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
        if(self.blockchain.lastBlock.blockID==block.prevBlockID):
            self.validateAndForward(block,event.time)

    # Event - 4
    def receiveBlock(self, event: Event):
        """
        Receive a Block.
        Validate and Update Chain if needed.
        """
        block = event.block
        if block.blockID in self.blockchain.rcvdBlocks:
            return
        self.validateAndForward(block,event.time)