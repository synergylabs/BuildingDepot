#!/bin/bash
set -euxo pipefail

echo "Please make sure you have downloaded the latest Building Depot version and are in the BD scripts folder! Press enter to confirm."
read response
cd ../
cd buildingdepot

# copy code files, excluding config files which are expected to already be in /srv/buildingdpot
sudo rsync -a . /srv/buildingdepot/ --exclude CentralReplica/config.py --exclude CentralService/cs_config --exclude DataService/ds_config

# restart services
sudo supervisorctl restart all
