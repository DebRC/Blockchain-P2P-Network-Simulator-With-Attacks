import sys
sys.path.append("../helper")
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
        self.n=n
        self.genesis = Block(blockID=1, prevBlockID=0, txnList=set(), prevLengthOfChain=0, miner=None, prevBlockBalance = [100]*n)
        # print(self.genesis)

        lowSpeed = [True for _ in range(int(n*z0))]+[False for _ in range(n-int(n*z0))]
        lowCPU = [True for _ in range(int(n*z1))]+[False for _ in range(n-int(n*z1))]
        randomGenerator.shuffle(lowSpeed)
        randomGenerator.shuffle(lowCPU)

        self.lowHashPower=1/(10*n-9*int(z1*n))
        self.highHashPower=10*self.lowHashPower

        mineTime=[I/self.lowHashPower if lowCPU[i] else I/self.highHashPower for i in range(n)]
        self.latencyMatrix = randomGenerator.uniform(10,500,[n,n])

        self.nodes = [None]*n
        for i in range(n):
            self.nodes[i] = Node(nodeID=i, lowSpeed=lowSpeed[i], lowCPU=lowCPU[i], mineTime=mineTime[i],genesisBlock=self.genesis,latencyMatrix=self.latencyMatrix)

        self.ttx = ttx
        self.I = I
        self.simTime=simTime

    def generateNetwork(self):
        while True:
            self.G = nx.Graph()
            self.G.add_nodes_from(range(self.n))
            for node in self.nodes:
                node.neighbors = set()
            for node in range(self.n):
                l = randomGenerator.integers(3, 7)
                # peers = set()
                for peer in range(self.n):
                    if peer!=node and len(self.nodes[peer].neighbors)<6 and len(self.nodes[node].neighbors)<l \
                        and peer not in self.nodes[node].neighbors and node not in self.nodes[peer].neighbors:
                        self.G.add_edge(node, peer)
                        self.nodes[node].neighbors.add(self.nodes[peer])
                        self.nodes[peer].neighbors.add(self.nodes[node])
            if nx.is_connected(self.G):
                break

    def generateTransaction(self):
        self.txnEventCounter=[]
        for p in self.nodes:
            t = randomGenerator.exponential(self.ttx)
            totalTxnEventCount=0
            while(t<=self.simTime):
                randomNode=self.nodes[randomGenerator.integers(0, len(self.nodes))]
                while(randomNode.nodeID==p.nodeID):
                    randomNode=self.nodes[randomGenerator.integers(0, len(self.nodes))]
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
                t+=randomGenerator.exponential(self.ttx)
            self.txnEventCounter.append(totalTxnEventCount)

    def generateBlock(self):
        i=0
        for p in self.nodes:
            t = i
            i+=1
            event=Event(time=t,type=2,receiverPeer=p)
            pushToEventQueue(event)


    def simulate(self):
        time = 0
        while(time<=self.simTime and globalEventQueue):
            time, event = popFromEventQueue()
            event.receiverPeer.eventHandler(event)
            
        while(globalEventQueue):
            time, event = popFromEventQueue()
            if event.type == 3 or event.type == 4:
                event.receiverPeer.eventHandler(event)

    def saveNetworkGraph(self): 
        plt.figure()
        nx.draw(self.G, with_labels=True)
        plt.savefig('outputs/graph.png')

    def saveBlockchainGraph(self):
        for node in self.nodes:
            plt.figure()
            nx.draw(node.g, pos=nx.kamada_kawai_layout(node.g), node_size=self.n, node_color='red')
            plt.savefig(f'./outputs/blockchain_node{node.nodeID}.png')

    def generateStats(self):
        for node in self.nodes:
            f=open(f"outputs/log_node{node.nodeID}.txt","w")
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
            # f.write("Total Mining Event:"+str(self.mineEventCounter[node.nodeID])+"\n")
            f.write("\n")
            totalBlocks=0
            totalBlocksInLongestChain=0
            f.write("**Blocks in the Blockchain**\n")
            for blockID in node.blockchain.rcvdBlocks:
                block=node.blockchain.rcvdBlocks[blockID]
                totalBlocks+=1
                f.write("Block ID:"+str(blockID)+","+"Previous Block ID:"+str(block.prevBlockID)+",")
                if(block.miner==None):
                    f.write("Miner ID: None")
                else:
                    f.write("Miner ID:"+str(block.miner.nodeID))
                f.write(","+"Number of TXNs:"+str(len(block.txnList))+",")
                f.write("Time:"+str(node.blockchain.rcvdBlocksTime[blockID]))
                f.write("\n")
            f.write("\n")
            f.write("**Blocks in the Longest Chain**\n")
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
                block = node.blockchain.rcvdBlocks[block.prevBlockID]
                if block.prevBlockID==0:
                    break
            f.write("\n")
            f.write("Total Blocks in the Chain:"+str(totalBlocks)+"\n")
            f.write("Total Blocks in the Longest Chain:"+str(totalBlocksInLongestChain)+"\n")
            f.write("\n")
            f.write(f"Blocks Mined - {node.blockCreated}\n")
            f.write(f"Blocks Mined in the Longest Chain - {blockMinedByNodeInChain}\n")
            f.close()
