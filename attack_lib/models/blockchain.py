from models.block import Block
class BlockChain:
    """
    Represents blockchain in a peer-to-peer network.

    Attributes:
    - rcvdTxns (dict<TxnID, Txn>): Map of all the received Transactions.
    - rcvdBlocks (dict<BlockID, Block>): Map of all the received Blocks.
    - rcvdBlocksTime (dict<BlockID, Time>): Map of the block IDs with time.
    - pendingBlocks (set(BlockID)): Map of all the block IDs which has not yet been processed.
    - orphanBlocks (set(BlockID)): Map of all the block IDs whose parent is not yet been in the chain.
    - invalidBlocks (set(BlockID)): Map of all the block IDs which has invalid txns.
    - lastBlock (Block): Reference to the last block.

    Methods:
    - __init__(): Initializes a Blockchain Object.
    - addGenesisBlock(genesisBlock): Adds the genensis block to the blockchain.
    - __str__(): Returns a human-readable string representation of blockchain.
    """
    def __init__(self):
        """
        Initializes a Blockchain Object.
        """
        self.rcvdTxns = set()

        self.rcvdBlocks = dict()
        self.rcvdBlocksTime = dict()

        self.pendingBlocks = set()
        self.orphanBlocks = set()
        self.invalidBlocks = set()

        self.lastBlock: Block=None

    def addGenesisBlock(self,genesisBlock):
        """
        Adds the genensis block to the blockchain.
        """
        self.rcvdBlocks[genesisBlock.blockID]=genesisBlock
        self.rcvdBlocksTime[genesisBlock.blockID]=0
        self.lastBlock=genesisBlock

    def __str__(self):
        res=[]
        for blockID in self.rcvdBlocks:
            res.append(str(self.rcvdBlocks[blockID].prevBlockID)+":"+blockID)
        print(res)
