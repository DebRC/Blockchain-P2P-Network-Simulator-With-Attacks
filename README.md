# P2P-Blockchain-Network-Simulator
A discrete-event blockchain simulator for a P2P cryptocurrency network.

## How to Run (Ubuntu/Debian)?
* Setup the Project - `bash setup.sh`
* Activate the Virtual Environment - `source venv/bin/activate`
* Run as default parameters - `python3 lib/main.py`

## How to change default parameters?
* number of nodes in the P2P network: `-n` or `--num_nodes`
* percentage of slow nodes: `-z0` or `--percentage_slow`
* percentage of nodes having low CPU power: `-z1` or `--percentage_lowcpu`
* mean inter-arrival time between transactions: `-ttx` or `--mean_inter_arrival`
* average time taken to mine a block: `-I` or `--average_block_mining_time`
* total time for which the P2P network is simulated: `-T` or `--simulation_time`

Example - `python3 main.py -n 10 -z0 0.5 -z1 0.5 -ttx 10 -I 600 -T 6000`

## Where are the simulation outputs saved?
Network graph, Blockchain graph and log for each node is saved inside `lib/outputs` folder after the end of simulation.
