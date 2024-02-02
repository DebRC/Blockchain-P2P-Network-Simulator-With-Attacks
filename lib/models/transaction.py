class Transaction:
    """
    Represents a transaction or mining operation in a peer-to-peer network.

    Attributes:
    - txnId (int): Unique identifier for the transaction.
    - val (float): Value associated with the transaction (e.g., amount of coins).
    - senderPeer (str): Identifier of the peer initiating the transaction or mining.
    - receiverPeer (str, optional): Identifier of the peer receiving the transaction (None for mining).
    - txnType (int): Type of the transaction (1 for payment, 2 for mining).
    - size (int): Size attribute for the transaction.

    Methods:
    - __init__(txnID, val, senderPeer, receiverPeer=None, txnType=1): Initializes a Transaction object.
    - __str__(): Returns a human-readable string representation of the transaction.
    """
    def __init__(self, txnID, val, senderPeer, receiverPeer=None, txnType=1) -> None:
        """
        Initializes a Transaction object.
        """
        self.txnId = txnID
        self.val = val        
        self.senderPeer = senderPeer
        self.receiverPeer = receiverPeer
        self.txnType = txnType
        self.size=1
        
    def __str__(self) -> str:
        """
        Returns a String Representation of the Transaction object.
        """
        if(self.txnType==1):
            return str(self.txnId)+":"+str(self.senderPeer)+" pays "+str(self.receiverPeer)+" "+str(self.val)+" coins"
        if(self.txnType==2):
            return str(self.txnId)+":"+str(self.senderPeer)+" mines "+str(self.val)+" coins"
        
