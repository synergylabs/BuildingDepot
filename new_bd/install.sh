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

# apt-get update

# # Install necessary packages
# apt-get install -y openssl python-setuptools python-dev build-essential python-software-properties
# apt-get install -y python-pip


# apt-get install -y nginx
cp configs/nginx.conf /etc/nginx/nginx.conf

# apt-get install -y supervisor 
# #apt-get install -y uwsgi uwsgi-plugin-python

# # MySQL
# apt-get install -y mysql-server libmysqlclient-dev python-mysqldb mysql-client-core-5.5

# # Redis
# apt-get install -y redis-server

# pip install --upgrade virtualenv

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
	cd /srv/buildingdepot
	# copy uwsgi files
	cp configs/uwsgi_cs.ini /etc/uwsgi/apps-available/cs.ini

	# Create supervisor config
	cp configs/supervisor-cs.conf /etc/supervisor/conf.d/

	# Create supervisor config for central replica
	cp configs/supervisor-replica.conf /etc/supervisor/conf.d/
	
	# Create nginx config
	rm -f /etc/nginx/sites-enabled/default
#	cp configs/nginx_cs.conf /etc/nginx/sites-available/cs.conf
#	ln -sf /etc/nginx/sites-available/cs.conf /etc/nginx/sites-enabled/cs.conf
}

function deploy_dataservice {
	setup_venv /srv/buildingdepot/
	
	#cp -r buildingdepot/DataService /srv/huaipeng/buildingdepot/
	

	cd /srv/buildingdepot

	# copy uwsgi files
	cp configs/uwsgi_ds.ini /etc/uwsgi/apps-available/ds.ini

	# Create supervisor config
	cp configs/supervisor-ds.conf /etc/supervisor/conf.d/

	# Create nginx config
	rm -f /etc/nginx/sites-enabled/default
#	cp configs/nginx_ds.conf /etc/nginx/sites-available/ds.conf
#	ln -sf /etc/nginx/sites-available/ds.conf /etc/nginx/sites-enabled/ds.conf
}


function joint_deployment_fix {
	# Create join nginx config
	rm -f /etc/nginx/sites-enabled/default
#	rm -f /etc/nginx/sites-enabled/ds.conf
#	rm -f /etc/nginx/sites-available/ds.conf
#	rm -f /etc/nginx/sites-enabled/cs.conf
#	rm -f /etc/nginx/sites-available/cs.conf
	cd /srv/buildingdepot
	cp configs/together.conf /etc/nginx/sites-available/together.conf
	ln -sf /etc/nginx/sites-available/together.conf /etc/nginx/sites-enabled/together.conf
}

function deploy_config {
	cp -r configs/ /srv/buildingdepot
	mkdir /var/sockets
}

function install_packages {
	apt-get update
	apt-get install
	apt-get -y install python-pip
	apt-get install -y mongodb
	apt-get install -y openssl python-setuptools python-dev build-essential python-software-properties
	apt-get install -y nginx
	apt-get install -y supervisor
	apt-get install -y redis-server
	pip install --upgrade virtualenv
	wget http://influxdb.s3.amazonaws.com/influxdb_0.9.2_amd64.deb
	sudo dpkg -i influxdb_0.9.2_amd64.deb
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
	#rm pip_packages.list
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

if [ "$DEPLOY_TOGETHER" = true ]; then
	joint_deployment_fix
	service nginx restart
fi

rm -rf configs

echo -e "\nInstallation Finished..\n"

