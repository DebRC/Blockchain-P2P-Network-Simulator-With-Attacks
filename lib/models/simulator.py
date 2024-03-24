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
import pandas as pd

class Simulator:
    def __init__(self, n, ttx, z0, z1, I,simTime):
        """
        Initializor for Simulator
        """

        if n<0 or ttx<0 or z0<0 or z0>1 or z1<0 or z1>1 or I<0 or simTime<0:
            raise ValueError("Invalid Parameters")

        print("Preparing Simulator ..")
        
        # Number of nodes
        self.n=n

        # Getting starting balance from json
        startingBalance = json.load(open(params_path))["starting-balance"]
        
        # Genesis block creation
        self.genesis = Block(blockID=1, prevBlockID=0, txnList=set(), prevLengthOfChain=0, miner=None, prevBlockBalance = [startingBalance]*self.n)

        # Picking random nodes for lowspeed and cpu
        lowSpeed = [True for _ in range(int(n*z0))]+[False for _ in range(n-int(n*z0))]
        lowCPU = [True for _ in range(int(n*z1))]+[False for _ in range(n-int(n*z1))]
        randomGenerator.shuffle(lowSpeed)
        randomGenerator.shuffle(lowCPU)

        # Calculating hashing power
        self.lowHashPower=1/(10*self.n-9*int(z1*self.n))
        self.highHashPower=10*self.lowHashPower

        # Calculating mine time
        mineTime=[I/self.lowHashPower if lowCPU[i] else I/self.highHashPower for i in range(self.n)]


        # Latency matrix of all the nodes
        low = json.load(open(params_path))["low-propagation-(ms)"]
        high = json.load(open(params_path))["high-propagation-(ms)"]
        self.latencyMatrix = randomGenerator.uniform(low,high,[self.n,self.n])

        # Creation of nodes
        self.nodes = [None]*self.n
        for i in range(self.n):
            self.nodes[i] = Node(nodeID=i, lowSpeed=lowSpeed[i], lowCPU=lowCPU[i], mineTime=mineTime[i],genesisBlock=self.genesis,latencyMatrix=self.latencyMatrix)

        totalHashingPower=0
        for node in self.nodes:
            print("NodeID:",node.nodeID,", Hashing Power:",I/node.mineTime, ", Mine Time:",node.mineTime)
            totalHashingPower+=I/node.mineTime
        print("Total Hashing Power:",totalHashingPower)

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
        t=0
        for p in self.nodes:
            event=Event(time=t,type=2,receiverPeer=p)
            pushToEventQueue(event)
            t+=1
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
            output_dir = os.path.dirname(os.path.abspath(__file__))
            outputs_path = os.path.join(output_dir, "../outputs/temp", f"graph_blockchain_node({node.nodeID}).txt")
            df = pd.read_csv(outputs_path)

            plt.figure()
            # Create a directed graph
            G = nx.DiGraph()

            # Add edges and nodes from the DataFrame
            for _, row in df.iterrows():
                G.add_node(row['block-id'], miner_id=row['miner-id'])
                # We don't add the genesis block (0) as it does not have a miner ID
                if row['prev-block-id'] != 0:
                    G.add_edge(row['block-id'],row['prev-block-id'])

            # Draw the graph
            plt.figure(figsize=(12, 10))
            pos = nx.kamada_kawai_layout(G)
            nx.draw(G, pos, node_color='blue', with_labels=False, edge_color='black', arrowsize=10, arrowstyle='-|>', node_size=200, font_size=10)
            plt.title('Blockchain Tree')
            output_dir = os.path.dirname(os.path.abspath(__file__))
            outputs_path = os.path.join(output_dir, "../outputs", f"blockchain_node({node.nodeID}).png")
            plt.savefig(outputs_path)
            plt.close()

        print("Blockchain figure for each node saved in outputs/blockchain_node(i).png\n")

    def writeBlockChain(self, f, node):
        """
        Writes the blockchain of the node specified\n
        in the file specified and in a csv file.\n
        Return: Total Blocks in the Blockchain, Blocks Mined by the Node
        """
        totalBlocks=0
        blocksMined=0
        for blockID in node.blockchain.rcvdBlocks:
            block=node.blockchain.rcvdBlocks[blockID]
            totalBlocks+=1
            f.write("Block ID:"+str(blockID)+","+"Previous Block ID:"+str(block.prevBlockID)+",")
            if(block.miner==None):
                f.write("Miner ID:None")
            else:
                f.write("Miner ID:"+str(block.miner.nodeID))
                if(block.miner.nodeID==node.nodeID):
                    blocksMined+=1
            f.write(","+"Number of TXNs:"+str(len(block.txnList))+",")
            f.write("Time:"+str(node.blockchain.rcvdBlocksTime[blockID]))
            f.write("\n")
        f.write("\n")

        output_dir = os.path.dirname(os.path.abspath(__file__))
        outputs_path = os.path.join(output_dir, "../outputs/temp", f"graph_blockchain_node({node.nodeID}).txt")
        f1=open(outputs_path,"w")
        f1.write("prev-block-id,block-id,miner-id\n")
        for blockID in node.blockchain.rcvdBlocks:
            block=node.blockchain.rcvdBlocks[blockID]
            if(block.miner==None):
                f1.write(str(block.prevBlockID)+","+str(blockID)+",-1\n")
            else:
                f1.write(str(block.prevBlockID)+","+str(blockID)+","+str(block.miner.nodeID)+"\n")
        f1.close()
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
            f.write(f"Hashing Power - {self.I/node.mineTime}\n")
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
