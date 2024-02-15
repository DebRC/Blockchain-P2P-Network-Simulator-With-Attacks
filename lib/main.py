from models.simulator import Simulator
from helper.utils import *
import argparse

parser = argparse.ArgumentParser(description='P2P Cryptocurrency Network Simulator')
parser.add_argument('-n', '--num_nodes', default=10, type=int, help='Number of Nodes in the Network')
parser.add_argument('-z0', '--percentage_slow', default=0.5, type=float, help='Percentage of Slow Nodes')
parser.add_argument('-z1', '--percentage_lowcpu', default=0.5, type=float, help='Percentage of Low Power Nodes')
parser.add_argument('-ttx', '--mean_inter_arrival', default=10, type=float, help='Mean Inter-Arrival Time Between Transactions')
parser.add_argument('-I', '--average_block_mining_time', default=600, type=float, help='Mean Time Taken to Mine a Block')
parser.add_argument('-T', '--simulation_time', default=6000, type=float, help='Time for Simulation')

args = parser.parse_args()

numNodes = args.num_nodes
z0 = args.percentage_slow
z1 = args.percentage_lowcpu
meanInterArrivalTime = args.mean_inter_arrival
meanMiningTime = args.average_block_mining_time
simTime = args.simulation_time

simulator = Simulator(numNodes, meanInterArrivalTime, z0, z1, meanMiningTime,simTime)
simulator.generateNetwork()
simulator.saveNetworkGraph()
simulator.generateTransaction()
simulator.generateBlock()
simulator.simulate()
simulator.saveBlockchainGraph()
simulator.generateStats()
