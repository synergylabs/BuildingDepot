#!/bin/bash

mkdir /etc/rabbitmq/ssl/
cp -rL --remove-destination <cert_path> /etc/rabbitmq/ssl/fullchain.pem
cp -rL --remove-destination <server_cert_path> /etc/rabbitmq/ssl/cert.pem
cp -rL --remove-destination <privkey_path> /etc/rabbitmq/ssl/privkey.pem
chmod -R 555 /etc/rabbitmq/ssl/
service rabbitmq-server restart