class Block:
    def __init__(self, blockID, prevBlockID, txnList, prevLengthOfChain, miner, balance):
        self.blockID = blockID
        self.prevBlockID = prevBlockID
        self.size = 1
        self.txnList = txnList
        self.balance = list(balance)
        self.miner = miner
        self.length = prevLengthOfChain+1
        
        for txn in self.txnList:
            self.size+=txn.size
        
        if self.size>1024:
            print(f"Size of Block Exceeded 1 MB")
            return None
        
        self.updateBalance()

    def updateBalance(self):
        for txn in self.txnList:
            if txn.type == 1:
                self.balance[txn.senderPeer.nodeID] -= txn.value
            self.balance[txn.receiverPeer.nodeID] += txn.value