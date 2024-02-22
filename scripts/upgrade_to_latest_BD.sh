#!/bin/bash

echo "Please make sure you have downloaded the latest Building Depot version and are in the BD scripts folder!"
read response
cd ../
cd buildingdepot
rm CentralReplica/config.py CentralService/cs_config DataService/ds_config
sudo cp -rf . /srv/buildingdepot/
sudo supervisorctl restart all
