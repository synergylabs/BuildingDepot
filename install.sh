#!/bin/bash

DEPLOY_TOGETHER=true
DEPLOY_CS=true
DEPLOY_DS=true

################################################################################
# Check and make sure we are running as root or sudo (?)
################################################################################
if [[ $UID -ne 0 ]]; then
	echo -e "\n$0 must be run as root. Most functions require super-user priviledges!\n"
	exit 1
fi

cp configs/nginx.conf /etc/nginx/nginx.conf

mkdir -p /srv/buildingdepot
mkdir -p /var/log/buildingdepot/CentralService
mkdir -p /var/log/buildingdepot/DataService
mkdir -p /var/sockets

# Deploy apps
function deploy_centralservice {
	setup_venv /srv/buildingdepot/
    
	#copy and untar new dataservice tarball
	cp -r buildingdepot/CentralService /srv/buildingdepot/
	cp -r buildingdepot/DataService /srv/buildingdepot/
	cp -r buildingdepot/CentralReplica /srv/buildingdepot/
	cp -r buildingdepot/OAuth2Server /srv/buildingdepot/
	cp -r buildingdepot/Documentation /srv/buildingdepot/
	cd /srv/buildingdepot
	# copy uwsgi files
	cp configs/uwsgi_cs.ini /etc/uwsgi/apps-available/cs.ini

	# Create supervisor config
	cp configs/supervisor-cs.conf /etc/supervisor/conf.d/

	# Create supervisor config for central replica
	cp configs/supervisor-replica.conf /etc/supervisor/conf.d/

	# Create nginx config
	rm -f /etc/nginx/sites-enabled/default
}

function deploy_dataservice {
	setup_venv /srv/buildingdepot/
	
	cd /srv/buildingdepot

	# copy uwsgi files
	cp configs/uwsgi_ds.ini /etc/uwsgi/apps-available/ds.ini

	# Create supervisor config
	cp configs/supervisor-ds.conf /etc/supervisor/conf.d/

	# Create nginx config
	rm -f /etc/nginx/sites-enabled/default
}


function joint_deployment_fix {
	# Create join nginx config
	rm -f /etc/nginx/sites-enabled/default
	cd /srv/buildingdepot
	cp configs/together.conf /etc/nginx/sites-available/together.conf
	ln -sf /etc/nginx/sites-available/together.conf /etc/nginx/sites-enabled/together.conf
}

function deploy_config {
	cp -r configs/ /srv/buildingdepot
	mkdir /var/sockets
}

function install_packages {
	echo 'deb http://www.rabbitmq.com/debian/ testing main' | sudo tee /etc/apt/sources.list.d/rabbitmq.list
	apt-get update
	apt-get install
	apt-get -y install python-pip
	apt-get install -y mongodb
	apt-get install -y openssl python-setuptools python-dev build-essential python-software-properties
	apt-get install -y nginx
	apt-get install -y supervisor
	apt-get install -y redis-server
	pip install --upgrade virtualenv
	apt-get install wget
	wget http://influxdb.s3.amazonaws.com/influxdb_0.9.2_amd64.deb
	sudo dpkg -i influxdb_0.9.2_amd64.deb
 	sudo apt-get install rabbitmq-server
}
 
function setup_venv {
	cp pip_packages.list $1
	cd $1

	virtualenv ./venv
	source venv/bin/activate

	pip install --upgrade pip
	pip install --upgrade setuptools
	pip install --upgrade -r pip_packages.list

	pip install --upgrade uWSGI
	mkdir -p /etc/uwsgi/apps-available/

	deactivate
	cd -
}

deploy_config
install_packages
if [ "$DEPLOY_CS" = true ]; then
	deploy_centralservice
fi

if [ "$DEPLOY_DS" = true ]; then
	deploy_dataservice
fi

/etc/init.d/mongodb start
service influxdb start
service supervisor stop
service supervisor start 
sleep 5
supervisorctl restart all
service influxdb start

if [ "$DEPLOY_TOGETHER" = true ]; then
	joint_deployment_fix
	service nginx restart
fi

rm -rf configs

curl -G http://localhost:8086/query --data-urlencode "q=CREATE DATABASE buildingdepot"
echo -e "\nInstallation Finished..\n"

