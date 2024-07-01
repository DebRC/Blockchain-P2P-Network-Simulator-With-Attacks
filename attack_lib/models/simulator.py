import sys
sys.path.append("../helper")
sys.path.append("../outputs")
from helper.utils import *
from models.event import Event
from models.transaction import Transaction
from models.block import Block
from models.node import Node
from models.selfish_node import SelfishNode
import random
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

class Simulator:
    def __init__(self, n_honest, zeta1, zeta2, ttx, I, simTime):
        """
        Initializor for Simulator
        """
        
        if n_honest<1 or ttx<0 or zeta1<0 or zeta1>1 or zeta2<0 or zeta2>1 or I<0 or simTime<0:
            raise ValueError("Invalid Parameters")

        print("Preparing Simulator ..")

        # Putting Hash Power of Selfish Miner in a List
        self.zetas=[]
        if zeta1>0:
            self.zetas.append(zeta1)
        if zeta2>0:
            self.zetas.append(zeta2)

        # Number of honest nodes
        self.n_honest=n_honest

        # Number of selfish nodes
        self.n_selfish=len(self.zetas)

        # Total number of nodes
        self.n=self.n_honest+self.n_selfish

        # Getting starting balance from json
        startingBalance = json.load(open(params_path))["starting-balance"]

        # Genesis block creation
        self.genesis = Block(blockID=1, prevBlockID=0, txnList=set(), prevLengthOfChain=0, miner=None, prevBlockBalance = [startingBalance]*self.n)

        # Making 50% of the honest nodes low speed
        lowSpeed = [True for _ in range(int(self.n_honest*0.5))]+[False for _ in range(self.n_honest-int(self.n_honest*0.5))]
        randomGenerator.shuffle(lowSpeed)

        # Calculating hashing power of honest node
        self.honestMinerHashPower=1
        for i in range(self.n_selfish):
            self.honestMinerHashPower-=self.zetas[i]
        # If Hashing Power is negative, raise error
        if self.honestMinerHashPower<0:
            raise ValueError("Invalid Hashing Power Input")
        self.honestMinerHashPower/=self.n_honest


        # Latency matrix of all the nodes
        low = json.load(open(params_path))["low-propagation-(ms)"]
        high = json.load(open(params_path))["high-propagation-(ms)"]
        self.latencyMatrix = randomGenerator.uniform(low,high,[self.n,self.n])

        # Creation of nodes
        self.nodes = [None]*self.n
        nodeID=0

        # Creation of honest nodes
        for _ in range(self.n_honest):
            self.nodes[nodeID] = Node(nodeID=nodeID, lowSpeed=lowSpeed[nodeID], mineTime=I/self.honestMinerHashPower,genesisBlock=self.genesis,latencyMatrix=self.latencyMatrix)
            nodeID+=1
        
        # Creation of selfish nodes
        for i in range(self.n_selfish):
            self.nodes[nodeID] = SelfishNode(nodeID=nodeID, lowSpeed=False, mineTime=I/self.zetas[i],genesisBlock=self.genesis,latencyMatrix=self.latencyMatrix)
            nodeID+=1

    
        for node in self.nodes:
            print("NodeID:",node.nodeID,", Hashing Power:",I/node.mineTime, ", Mine Time:",node.mineTime)
        
        print("Total Hashing Power:",self.honestMinerHashPower*self.n_honest+sum(self.zetas))

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
                # Select peer but make sure no. of edges does not exceed 6
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

        for node in self.nodes[self.n_honest:]:
            node.releaseChain()
            
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

            # Prepare color map
            color_map = []
            for nodex in G:
                miner_id = G.nodes[nodex]['miner_id']
                if miner_id == self.n_honest:
                    color_map.append('blue')  # Miner ID 10 -> Blue
                elif miner_id == self.n_honest+1:
                    color_map.append('red')  # Miner ID 11 -> Red
                else:
                    color_map.append('grey')  # Other -> Grey

            # Draw the graph
            plt.figure(figsize=(12, 10))
            pos = nx.kamada_kawai_layout(G)  # For consistent layout between runs
            nx.draw(G, pos, node_color=color_map, with_labels=False, edge_color='black', arrowsize=10, arrowstyle='-|>', node_size=200, font_size=10)
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
        f=open(outputs_path,"w")
        f.write("prev-block-id,block-id,miner-id\n")
        for blockID in node.blockchain.rcvdBlocks:
            block=node.blockchain.rcvdBlocks[blockID]
            if(block.miner==None):
                f.write(str(block.prevBlockID)+","+str(blockID)+",-1\n")
            else:
                f.write(str(block.prevBlockID)+","+str(blockID)+","+str(block.miner.nodeID)+"\n")
        f.close()

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
            f.write("\n")
            if node in self.nodes[self.n_honest:]:
                if blockMined!=0:
                    f.write(f"MPU(adv)={blockMinedByNodeInChain/blockMined}\n")
                else:
                    f.write(f"MPU(adv)=0\n")
            if totalBlocks!=0:
                f.write(f"MPU(overall)={totalBlocksInLongestChain/totalBlocks}\n")
            else:
                f.write(f"MPU(overall)=0\n")
            f.close()
        print("Stats Generated. Saved in outputs/log_node(i).txt\n")
