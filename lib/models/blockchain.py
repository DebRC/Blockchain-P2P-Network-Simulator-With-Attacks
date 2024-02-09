from models.block import Block
class BlockChain:
    def __init__(self):
        self.rcvdBlocks = dict()
        self.rcvdTxns = dict()
        self.rcvdBlocksTime = dict()

        self.pendingBlocks = set()
        self.pendingTxns = set()
        self.orphanBlocks = set()
        self.invalidBlocks = set()

        self.lastBlock: Block=None

    def addGenesisBlock(self,genesisBlock):
        self.rcvdBlocks[genesisBlock.blockID]=genesisBlock
        self.lastBlock=genesisBlock
