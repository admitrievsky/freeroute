#!/bin/bash

set -e

if [ "$EUID" -ne 0 ]
  then echo "Please run with sudo"
  exit
fi

echo 'This script assumes you are running it on a fresh install of Debian 11/12'
echo 'The script should be run as ordinal user with sudo command'
echo ''
echo 'This script will do the following:'
echo '1. Install the required packages'
echo '2. Install the required python packages'
echo '3. Test run of the OpenVPN connection, and if successful, extract gateway address'
echo '4. Install OpenVPN connection as a service'
echo '5. Install nftables rules to /etc/nftables.conf. This will overwrite any existing rules!'
echo '6. Enable IPv4 forwarding'
echo '7. Config sudoers to allow running ip command as root'
echo '8. Install freeroute script as a service'

echo 'Do you wish to continue? (y/n)'
read answer
if [ "$answer" == "${answer#[Yy]}" ] ;then
    echo 'Exiting...'
    exit 1
fi

echo 'Updating packages'
apt update

echo 'Installing required packages...'
apt install -y python3-pip python3-venv openvpn nftables

echo 'Installing virtual environment and python packages...'
python3 -m venv .venv
source .venv/bin/activate
pip install poetry
cd service
poetry install
cd ..

python3 service/installer.py $@
