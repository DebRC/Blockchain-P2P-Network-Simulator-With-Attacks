from transaction import Transaction
from node import Node

class Block:
    def __init__(self, blockID, parentBlockID, txnList, miner, balance=[]):
        self.blockID = blockID
        self.parentBlockID = parentBlockID
        self.size = 1
        self.txnList = txnList
        self.balance = list(balance)
        self.miner = miner
        
        for txn in self.txnList:
            self.size+=txn.size
        
        if self.size>1000:
            raise ValueError(f"Size of Block Exceeded 1 MB")
        
        for txn in self.txnList:
            if txn.type == 1:
                self.balance[txn.senderPeer.nodeID] -= txn.value
            self.balance[txn.receiverPeer.nodeID] += txn.value