# Blockchain-P2P-Network-Simulator-With-Attacks
A discrete-event blockchain simulator for a P2P cryptocurrency network with capability of PoW performance analysis and simulation of Selfish Mining attack.
<p align="center">
  <img width="250" height="150" src="https://github.com/DebRC/Blockchain-P2P-Network-Simulator-With-Attacks/assets/63597606/b2a83720-0cc4-4fc8-98a3-8afca7f9e651">
</p>

## Project Structure
* The project is divided into two folders.
* `normal_lib` contains the code for running a blockchain simulator with various configurable parameters without attacks.
* `attack_lib` contains the code for running a blockchain simulator with multiple clients acting as Selfish Miner.
* `Normal-Report.pdf` and `Attack-Report.pdf` contains a performance analysis of both the simulators with detailed explanation.

## How to run Normal Simulator(Ubuntu/Debian)?
* Setup the Project - `bash setup.sh`
* Activate the Virtual Environment - `source venv/bin/activate`
* Run simulator with default parameters - `python3 normal_lib/main.py`
### How to change default parameters?
* Number of nodes in the P2P network: `-n` or `--num_nodes`
* Percentage of slow nodes: `-z0` or `--percentage_slow`
* Percentage of nodes having low CPU power: `-z1` or `--percentage_lowcpu`
* Mean inter-arrival time between transactions: `-ttx` or `--mean_inter_arrival`
* Average time taken to mine a block: `-I` or `--average_block_mining_time`
* Total time for which the P2P network is simulated: `-T` or `--simulation_time`
* Example - `python3 main.py -n 10 -z0 0.5 -z1 0.5 -ttx 10 -I 600 -T 6000`

## How to run Selfish Attack Simulator(Ubuntu/Debian)?
* Setup the Project - `bash setup.sh`
* Activate the Virtual Environment - `source venv/bin/activate`
* Run simulator with default parameters - `python3 attack_lib/main.py`
### How to change default parameters?
* Number of honest nodes in the P2P network: `-n` or `--num_honest_nodes`
* Hashing Power of first Selfish Node: `-z1` or `--zeta1`
* Hashing Power of second Selfish Node: `-z2` or `--zeta2`
* Mean inter-arrival time between transactions: `-ttx` or `--mean_inter_arrival`
* Average time taken to mine a block: `-I` or `--average_block_mining_time`
* total time for which the P2P network is simulated: `-T` or `--simulation_time`
* Example - `python3 main.py -n 10 -z1 0.3 -z2 0.3 -ttx 10 -I 300 -T 6000`

## Where are the simulation outputs saved?
Network graph, Blockchain graph and log for each node is saved inside `normal_lib/outputs` and `attack_lib/outputs` folder after the end of simulation.

## Simulator-Design
![Design-Doc](https://github.com/DebRC/Blockchain-P2P-Network-Simulator-With-Attacks/assets/63597606/91415115-dfa2-43f3-902e-14f1579b74b3)
