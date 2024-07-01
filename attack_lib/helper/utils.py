import os
import heapq
import json
from numpy.random import default_rng

script_dir = os.path.dirname(os.path.abspath(__file__))
params_path = os.path.join(script_dir, 'params.json')

randomGenerator=None
txnID=-1
blockID=1
totalBlocks=0
globalEventQueue=[]

def initialize_rand_generator(seed=None):
    global randomGenerator
    if not seed:
        seed = json.load(open(params_path))['default-seed']
    randomGenerator=default_rng(seed)

def generateTransactionID():
    global txnID
    txnID+=1
    return txnID

def generateBlockID():
    global blockID
    blockID+=1
    return blockID

def pushToEventQueue(event):
    heapq.heappush(globalEventQueue, (event.time, event))

def popFromEventQueue():
    return heapq.heappop(globalEventQueue)

def incrementTotalBlocks():
    global totalBlocks
    totalBlocks += 1

initialize_rand_generator()