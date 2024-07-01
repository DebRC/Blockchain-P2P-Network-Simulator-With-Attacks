from models.transaction import Transaction
import json,os

class Block:
    """
    Represents a Block (A set of transactions) in a peer-to-peer cryptocurrency network.

    Attributes:
    - blockID (int): Unique identifier for the block.
    - prevBlockID (int): Unique identifier of the previous block this block is pointing to.
    - txnList (set[Transaction]): Set of unique transactions this block is storing.
    - prevLengthOfChain (int): Length of the chain of the previous block.
    - miner (Node): Node object who mined this block.
    - balance (list[float]): Previous balance of the nodes before this node is constructed.

    Methods:
    - __init__(txnID, val, senderPeerID, receiverPeerID, type=0): Initializes a Transaction object.
    - __str__(): Returns a human-readable string representation of the transaction.
    """
    def __init__(
        self,
        blockID: int,
        prevBlockID: int,
        txnList: set[Transaction],
        prevLengthOfChain: int,
        miner,
        prevBlockBalance: list[float]
    ):
        self.blockID: int = blockID
        self.prevBlockID: int = prevBlockID
        self.size: int = 0
        self.balance: list[float] = list(prevBlockBalance)
        self.miner = miner
        self.length: int = prevLengthOfChain + 1
        self.txnList: set[Transaction] = txnList

        for txn in self.txnList:
            self.size += txn.size

        self.updateBalance()

    # Update the present balance of the block
    def updateBalance(self):
        for txn in self.txnList:
            if txn.type == 0:
                self.balance[txn.senderPeerID] -= txn.val
            self.balance[txn.receiverPeerID] += txn.val
        
    def __str__(self):
        res=""
        res+="BlockID:"+str(self.blockID)+"\n"
        res+="Previous BlockID:"+str(self.prevBlockID)+"\n"
        res+="Transaction List : "+ str([str(txn) for txn in self.txnList])+"\n"
        res+="Balance:"+str(self.balance)
        return res