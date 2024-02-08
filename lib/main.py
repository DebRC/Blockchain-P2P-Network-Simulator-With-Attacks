from models.simulator import Simulator
from helper.utils import *

numNodes = 10
meanInterArrivalTime=10
z0=0.3
z1=0.3
meanMiningTime=600
simTime=5000

simulator = Simulator(numNodes, meanInterArrivalTime, z0, z1, meanMiningTime,simTime)
simulator.generateNetwork()
simulator.saveNetworkGraph()
simulator.generateTransaction()
simulator.simulate()
simulator.drawBlockchain()