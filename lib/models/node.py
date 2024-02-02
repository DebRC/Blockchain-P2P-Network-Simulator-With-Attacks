import sys
sys.path.append("../helper")
from utils import *

class Node:
    def __init__(
        self,
        nodeID,
        genesisBlock,
        hashingPower,
        blockIDGenerator,
        txnIDGen,
        slowSpeed=False,
        lowCPU=False,
        interArrivalTime=0,
    ):
        self.nodeID = nodeID
        self.slowSpeed = slowSpeed
        self.lowCPU = lowCPU
        self.hashingPower = hashingPower
        self.interArrivalTime = interArrivalTime
        self.lastBlockID = genesisBlock.blockID

        self.blockIDGenerator=blockIDGenerator
        self.txnIDGen=txnIDGen

        self.neighbors = set()
        self.blockchain = dict()
        self.blockReceived = set()
        self.blockTime = dict()
        self.orphanBlocks = set()
        self.txnReceived = set()
        self.txnIncluded = set()

        self.blockchain[genesisBlock.blockID] = genesisBlock
        self.blockReceived.add(genesisBlock)
        self.blockTime[genesisBlock.blockID] = 0

