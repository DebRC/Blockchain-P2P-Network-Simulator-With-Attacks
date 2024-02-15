# P2P-Cryptocurrency-Network-Simulator
A discrete-event simulator for a P2P cryptocurrency network.

# How to Run?
* Optional Step: Create a virtual environment in Python
	* Install virtualenv - `pip3 install virtualenv`
	* Create a virtualenv in project folder - `virtualenv env`
	* Activate the virtualenv - `source env/bin/activate`
* Install the requirements - `pip3 install -r requirements.txt`
* Run as default parameters - `python3 lib/main.py`

## How to change default parameters?
* number of nodes in the P2P network: `-n` or `--num_nodes`
* percentage of slow nodes: `-z0` or `--percentage_slow`
* percentage of nodes having low CPU power: `-z1` or `--percentage_lowcpu`
* mean inter-arrival time between transactions: `-ttx` or `--mean_inter_arrival`
* average time taken to mine a block: `-I` or `--average_block_mining_time`
* total time for which the P2P network is simulated: `-T` or `--simulation_time`

Example - `python3 main.py -n 10 -z0 0.5 -z1 0.5 -ttx 10 -I 600 -T 6000`

## Where are the outputs saved?
Network graph, Blockchain graph and log for each node is saved inside `lib/outputs` folder after the end of simulation.
