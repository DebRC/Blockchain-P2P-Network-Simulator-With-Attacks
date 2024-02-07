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
        self.genesis = Block(blockID=1, prevBlockID=0, txnList=set(), prevLengthOfChain=0, miner=None, balance = [0]*n, txnPool=set())
        # print(self.genesis)

        lowSpeed = [True for i in range(int(n*z0))]+[False for i in range(n-int(n*z0))]
        lowCPU = [True for i in range(int(n*z1))]+[False for i in range(n-int(n*z1))]

        highHashPower=10/(10*n-9*int(z1*n))
        lowHashPower=1/(10*n-9*int(z1*n))

        mineTime=[lowHashPower if lowCPU[i] else highHashPower for i in range(n)]

        self.nodes = [None]*n
        for i in range(n):
            self.nodes[i] = Node(nodeID=i, lowSpeed=lowSpeed[i], lowCPU=lowCPU[i], mineTime=mineTime[i],genesisBlock=self.genesis)

        self.ttx = ttx
        self.I = I
        self.simTime=simTime
        generateLatencyMatrix(n)

    def generateNetwork(self):
        graphGenerated=False
        while(not graphGenerated):
            self.G = nx.Graph()
            self.G.add_nodes_from(range(self.n))
            for node in self.nodes:
                node.neighbors = set()
            for node in range(self.n):
                l = randomGenerator.integers(3, 7)
                peers = random.sample(set(range(self.n)) - {node}, l)
                for peer in peers:
                    if(peer not in self.nodes[node].neighbors and node not in self.nodes[peer].neighbors):
                        self.G.add_edge(node, peer)
                        self.nodes[node].neighbors.add(self.nodes[peer])
                        self.nodes[peer].neighbors.add(self.nodes[node])
            graphGenerated=True
            for node in range(self.n):
                if len(self.nodes[node].neighbors) not in range(3,7):
                    graphGenerated=False
                    break
            if not nx.is_connected(self.G):
                graphGenerated=False
        for node in range(self.n):
            res=[]
            for p in self.nodes[node].neighbors:
                res.append(p.nodeID)
            print(node,":",res)
        print(self.G)
                        

    def generateTransaction(self):
        for p in self.nodes:
            t = randomGenerator.exponential(self.ttx)
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
                t+=randomGenerator.exponential(self.ttx)

    def simulate(self):
        time = 0
        while(time<=self.simTime and globalEventQueue):
            time, event = popFromEventQueue()
            event.receiverPeer.eventHandler(event)

    def saveNetworkGraph(self): 
        plt.figure()
        nx.draw(self.G, with_labels=True)
        plt.savefig('graph.png')