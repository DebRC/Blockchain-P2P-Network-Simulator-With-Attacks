import json, os

class Transaction:
    """
    Represents a transaction or mining operation in a peer-to-peer network.

    Attributes:
    - txnId (int): Unique identifier for the transaction.
    - val (float): Value associated with the transaction (e.g., amount of coins).
    - senderPeerID (int): Identifier of the peer initiating the transaction or mining (-1 for mining).
    - receiverPeerID (int): Identifier of the peer receiving the transaction.
    - type (int, optional): Type of the transaction (0 for payment, 1 for mining).
    - size (int): Size attribute for the transaction.

    Methods:
    - __init__(txnID, val, senderPeerID, receiverPeerID, type=0): Initializes a Transaction object.
    - __str__(): Returns a human-readable string representation of the transaction.
    """
    def __init__(self, txnID, val, senderPeerID, receiverPeerID, type=0) -> None:
        """
        Initializes a Transaction object.
        """
        self.txnID = txnID
        self.val = val        
        self.senderPeerID = senderPeerID
        self.receiverPeerID = receiverPeerID
        self.type = type

        script_dir = os.path.dirname(os.path.abspath(__file__))
        params_path = os.path.join(script_dir,"../helper",'params.json')
        self.size = json.load(open(params_path))['txn-size']
        
    def __str__(self) -> str:
        """
        Returns a String Representation of the Transaction object.
        """
        if(self.type==0):
            return str(self.txnID)+":"+str(self.senderPeerID)+" pays "+str(self.receiverPeerID)+" "+str(self.val)+" coins"
        if(self.type==1):
            return str(self.txnID)+":"+str(self.receiverPeerID)+" mines "+str(self.val)+" coins"