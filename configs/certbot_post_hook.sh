#!/bin/bash

mkdir /etc/rabbitmq/ssl/
cp -rL --remove-destination /etc/letsencrypt/live/dev-buildingdepot-synergy.mites.io/fullchain.pem /etc/rabbitmq/ssl/fullchain.pem
cp -rL --remove-destination /etc/letsencrypt/live/dev-buildingdepot-synergy.mites.io/cert.pem /etc/rabbitmq/ssl/cert.pem
cp -rL --remove-destination /etc/letsencrypt/live/dev-buildingdepot-synergy.mites.io/privkey.pem /etc/rabbitmq/ssl/privkey.pem
chmod -R 555 /etc/rabbitmq/ssl/
service rabbitmq-server restart