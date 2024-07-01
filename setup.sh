#!/bin/bash

# Install virtualenv using apt package manager
echo "Installing Python3 Virtual Environement..."
sudo apt install python3-virtualenv
echo "Python3 Virtual Environement Installed"

# Create a virtual environment in the project folder
echo "Creating a Virtual Environement..."
virtualenv venv
echo "Virtual Environement Created"

echo "Installing Dependencies..."
# Activate the virtual environment
source venv/bin/activate

# Install dependencies from requirements.txt
pip3 install -r requirements.txt

# Create the necessary folders
mkdir -p normal_lib/outputs/temp
mkdir -p attack_lib/outputs/temp

echo "Setup Completed"
