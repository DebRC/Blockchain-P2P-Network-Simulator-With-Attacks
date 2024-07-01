from models.simulator import Simulator
from helper.utils import *
import argparse

parser = argparse.ArgumentParser(description="P2P Cryptocurrency Network Simulator")
parser.add_argument(
    "-n",
    "--num_honest_nodes",
    default=10,
    type=int,
    help="Number of Honest Nodes in the Network",
)
parser.add_argument(
    "-z1", "--zeta1", default=0.3, type=float, help="Mining Power of Selfish Node 1"
)
parser.add_argument(
    "-z2", "--zeta2", default=0.3, type=float, help="Mining Power of Selfish Node 2"
)
parser.add_argument(
    "-ttx",
    "--mean_inter_arrival",
    default=10,
    type=float,
    help="Mean Inter-Arrival Time Between Transactions",
)
parser.add_argument(
    "-I",
    "--average_block_mining_time",
    default=300,
    type=float,
    help="Mean Time Taken to Mine a Block",
)
parser.add_argument(
    "-T", "--simulation_time", default=6000, type=float, help="Time for Simulation"
)

args = parser.parse_args()

numHonestNodes = args.num_honest_nodes
z1 = args.zeta1
z2 = args.zeta2
meanInterArrivalTime = args.mean_inter_arrival
meanMiningTime = args.average_block_mining_time
simTime = args.simulation_time

simulator = Simulator(
    numHonestNodes, z1, z2, meanInterArrivalTime, meanMiningTime, simTime
)
simulator.generateNetwork()
simulator.saveNetworkGraph()
simulator.generateTransaction()
simulator.generateBlock()
simulator.simulate()
simulator.generateStats()
simulator.saveBlockchainGraph()