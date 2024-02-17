import sys
sys.path.append("../helper")
sys.path.append("../outputs")
from helper.utils import *
from models.event import Event
from models.transaction import Transaction
from models.block import Block
from models.node import Node
import random
import networkx as nx
import matplotlib.pyplot as plt

class Simulator:
    def __init__(self, n, ttx, z0, z1, I,simTime):
        """
        Initializor for Simulator
        """
        print("Preparing Simulator ..")
        self.n=n

        # Getting starting balance from json
        startingBalance = json.load(open(params_path))["starting-balance"]
        # Genesis block creation
        self.genesis = Block(blockID=1, prevBlockID=0, txnList=set(), prevLengthOfChain=0, miner=None, prevBlockBalance = [startingBalance]*n)

        # Picking random nodes for lowspeed and cpu
        lowSpeed = [True for _ in range(int(n*z0))]+[False for _ in range(n-int(n*z0))]
        lowCPU = [True for _ in range(int(n*z1))]+[False for _ in range(n-int(n*z1))]
        randomGenerator.shuffle(lowSpeed)
        randomGenerator.shuffle(lowCPU)

        # Calculating hashing power
        self.lowHashPower=1/(10*n-9*int(z1*n))
        self.highHashPower=10*self.lowHashPower

        # Calculating mine time
        mineTime=[I/self.lowHashPower if lowCPU[i] else I/self.highHashPower for i in range(n)]

        # Latency matrix of all the nodes
        self.latencyMatrix = randomGenerator.uniform(10,500,[n,n])

        # Creation of nodes
        self.nodes = [None]*n
        for i in range(n):
            self.nodes[i] = Node(nodeID=i, lowSpeed=lowSpeed[i], lowCPU=lowCPU[i], mineTime=mineTime[i],genesisBlock=self.genesis,latencyMatrix=self.latencyMatrix)

        self.ttx = ttx
        self.I = I
        self.simTime=simTime
        print("Simulator Prepared\n")

    def generateNetwork(self):
        """
        Generate a graph of N nodes\n
        N specified at init
        """
        print("Generating Graph ..")
        while True:
            self.G = nx.Graph()
            self.G.add_nodes_from(range(self.n))
            for node in self.nodes:
                node.neighbors = set()
            for node in range(self.n):
                # Number of peers = l (Should be between 3 and 6)
                l = randomGenerator.integers(3, 7)
                nums=list(range(self.n))
                random.shuffle(nums)
                # Select peer but make sure no. of edges does not exceed 6S
                for peer in nums:
                    if peer!=node and len(self.nodes[peer].neighbors)<6 and len(self.nodes[node].neighbors)<l \
                        and peer not in self.nodes[node].neighbors and node not in self.nodes[peer].neighbors:
                        self.G.add_edge(node, peer)
                        self.nodes[node].neighbors.add(self.nodes[peer])
                        self.nodes[peer].neighbors.add(self.nodes[node])
            # If graph created is connected break
            if nx.is_connected(self.G):
                break
        print("Graph Generated\n")

    def generateTransaction(self):
        """
        Generate event with transaction timestamps 
        for each node
        """
        print("Generating Transaction Timestamps ..")
        self.txnEventCounter=[]
        for p in self.nodes:
            # Transaction gen time
            t = randomGenerator.exponential(self.ttx)
            totalTxnEventCount=0
            while(t<=self.simTime):
                # Receiver node should be random
                randomNode=self.nodes[randomGenerator.integers(0, len(self.nodes))]
                while(randomNode.nodeID==p.nodeID):
                    randomNode=self.nodes[randomGenerator.integers(0, len(self.nodes))]
                # Create transaction and event
                eventTXN = Transaction(
                    txnID= generateTransactionID(),
                    senderPeerID=p.nodeID,
                    receiverPeerID = randomNode.nodeID,
                    val=0,
                    type=0
                )
                event=Event(time=t,type=0,senderPeer=p,receiverPeer=randomNode,txn=eventTXN)
                pushToEventQueue(event=event)
                totalTxnEventCount+=1

                # Add time for next transaction
                t+=randomGenerator.exponential(self.ttx)
            self.txnEventCounter.append(totalTxnEventCount)
        print("Transaction Timestamps Generated\n")

    def generateBlock(self):
        """
        Generate first mining event for each node
        """
        print("Generating First Mining Timestamp for each Node ..")
        i=0
        for p in self.nodes:
            t = i
            i+=1
            event=Event(time=t,type=2,receiverPeer=p)
            pushToEventQueue(event)
        print("Mining Timestamps Generated\n")


    def simulate(self):
        """
        Start simulation
        """
        print("Event Simulator Started ..")
        time = 0
        while(time<=self.simTime and globalEventQueue):
            time, event = popFromEventQueue()
            event.receiverPeer.eventHandler(event)
            
        while(globalEventQueue):
            time, event = popFromEventQueue()
            if event.type == 3 or event.type == 4:
                event.receiverPeer.eventHandler(event)
        print("Event Simulator Finished\n")

    def saveNetworkGraph(self): 
        """
        Save the network graph generated
        """
        output_dir = os.path.dirname(os.path.abspath(__file__))
        outputs_path = os.path.join(output_dir, "../outputs", "graph.png")
        plt.figure()
        nx.draw(self.G, with_labels=True)
        plt.savefig(outputs_path)
        print("Graph figure saved in outputs/graph.png\n")

    def saveBlockchainGraph(self):
        """
        Save the blockchain graph
        """
        for node in self.nodes:
            plt.figure()
            nx.draw(node.g, pos=nx.kamada_kawai_layout(node.g), node_size=self.n, node_color='red')
            output_dir = os.path.dirname(os.path.abspath(__file__))
            outputs_path = os.path.join(output_dir, "../outputs", f"blockchain_node({node.nodeID}).png")
            plt.savefig(outputs_path)
        print("Blockchain figure for each node saved in outputs/blockchain_node(i).png\n")

    def writeBlockChain(self, f, node):
        """
        Writes the blockchain of the node specified\n
        in the file specified.\n
        Return: Total Blocks in the Blockchain, Blocks Mined by the Node
        """
        totalBlocks=0
        blocksMined=0
        for blockID in node.blockchain.rcvdBlocks:
            block=node.blockchain.rcvdBlocks[blockID]
            totalBlocks+=1
            f.write("Block ID:"+str(blockID)+","+"Previous Block ID:"+str(block.prevBlockID)+",")
            if(block.miner==None):
                f.write("Miner ID: None")
            else:
                f.write("Miner ID:"+str(block.miner.nodeID))
                if(block.miner.nodeID==node.nodeID):
                    blocksMined+=1
            f.write(","+"Number of TXNs:"+str(len(block.txnList))+",")
            f.write("Time:"+str(node.blockchain.rcvdBlocksTime[blockID]))
            f.write("\n")
        f.write("\n")
        return totalBlocks,blocksMined

    def writeLongestChain(self, f, node):
        """
        Writes the longest chain in the blockchain\n
        of the node specified in the file specified.\n
        Return: Total Blocks in the Blockchain, Blocks Mined by the Node
        """
        totalBlocksInLongestChain=0
        blockMinedByNodeInChain=0
        block = node.blockchain.lastBlock
        while(True):
            f.write("Block ID:"+str(block.blockID)+","+"Previous Block ID:"+str(block.prevBlockID)+",")
            totalBlocksInLongestChain+=1
            if(block.miner==None):
                f.write("Miner ID: None")
            else:
                f.write("Miner ID:"+str(block.miner.nodeID))
                if block.miner.nodeID==node.nodeID:
                    blockMinedByNodeInChain+=1
            f.write(","+"Number of TXNs:"+str(len(block.txnList))+",")
            f.write("Time:"+str(node.blockchain.rcvdBlocksTime[block.blockID]))
            f.write("\n")
            if block.blockID==1:
                break
            block = node.blockchain.rcvdBlocks[block.prevBlockID]
        f.write("\n")
        return totalBlocksInLongestChain,blockMinedByNodeInChain

    def generateStats(self):
        print("Generating Stats ..")
        for node in self.nodes:
            output_dir = os.path.dirname(os.path.abspath(__file__))
            outputs_path = os.path.join(output_dir, "../outputs", f"log_node({node.nodeID}).txt")
            f=open(outputs_path,"w")
            if node.lowCPU:
                f.write(f"Hashing Power - {self.lowHashPower}\n")
            else:
                f.write(f"Hashing Power - {self.highHashPower}\n")
            if node.lowSpeed:
                f.write(f"Speed - Low\n")
            else:
                f.write(f"Speed - High\n")
            f.write("\n")
            f.write("Total Transaction Event:"+str(self.txnEventCounter[node.nodeID])+"\n")
            f.write("\n")
            f.write("**Blocks in the Blockchain**\n")
            totalBlocks,blockMined=self.writeBlockChain(f,node)
            f.write("**Blocks in the Longest Chain**\n")
            totalBlocksInLongestChain,blockMinedByNodeInChain=self.writeLongestChain(f,node)                
            f.write("Total Blocks in the Chain:"+str(totalBlocks)+"\n")
            f.write("Total Blocks in the Longest Chain:"+str(totalBlocksInLongestChain)+"\n")
            f.write("\n")
            f.write(f"Blocks Mined - {blockMined}\n")
            f.write(f"Blocks Mined in the Longest Chain - {blockMinedByNodeInChain}\n")
            f.close()
        print("Stats Generated. Saved in outputs/log_node(i).txt\n")
