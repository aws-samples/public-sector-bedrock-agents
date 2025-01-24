#!/bin/bash

# Amazon 2023 Linux Setup

# 1. Install available package and OS updates
echo "Updating system packages..."
sudo dnf update -y

# 2. Install and setup Docker on Amazon Linux 2023
echo "Installing Docker..."
sudo dnf -y install docker

# Add group membership for the default ec2-user
echo "Adding ec2-user to the docker group..."
sudo usermod -a -G docker ec2-user

# Start and enable the docker service
echo "Enabling and starting Docker service..."
sudo systemctl enable docker.service
sudo systemctl start docker.service

# 3. Install Python 3.11
echo "Installing Python 3.11..."
sudo dnf -y install python3.11

# 4. Install Git
echo "Installing Git..."
sudo dnf -y install git

# 5. Install NodeJS
echo "Installing NodeJS..."
sudo dnf -y install nodejs

# 6. Install CDK
echo "Installing AWS CDK..."
sudo npm install -g aws-cdk

# Set up Python aliases
echo "Setting up Python aliases..."

# Check if ~/.bash_aliases exists
if [ -f ~/.bash_aliases ]; then
    echo "~/.bash_aliases already exists. Appending aliases if not already present."
else
    touch ~/.bash_aliases
fi

# Define the aliases
alias_python="alias python=/usr/bin/python3.11"
alias_python3="alias python3=/usr/bin/python3.11"

# Add the aliases to ~/.bash_aliases if they don't already exist
if ! grep -q "python=/usr/bin/python3.11" ~/.bash_aliases; then
    echo "\$alias_python" >> ~/.bash_aliases
fi
if ! grep -q "python3=/usr/bin/python3.11" ~/.bash_aliases; then
    echo "\$alias_python3" >> ~/.bash_aliases
fi

# Inform the user that the aliases have been added
echo "Aliases have been added to ~/.bash_aliases"

# Source the ~/.bash_aliases file to apply changes immediately
source ~/.bash_aliases

echo "Setup complete."