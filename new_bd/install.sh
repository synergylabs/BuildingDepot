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


# delete existing centralservice
rm -rf /srv/huaipeng/buildingdepot
rm -rf /var/log/huaipeng

mkdir -p /srv/huaipeng/buildingdepot
mkdir -p /var/log/huaipeng/buildingdepot/CentralService
mkdir -p /var/log/huaipeng/buildingdepot/DataService

# Deploy apps
function deploy_centralservice {
	setup_venv /srv/huaipeng/buildingdepot/

	#copy and untar new dataservice tarball
	cp -r CentralService /srv/huaipeng/buildingdepot/

	cd /home/huaipeng/buildingdepot
	# copy uwsgi files
	cp configs/uwsgi_huaipeng_cs.ini /etc/uwsgi/apps-available/huaipeng_cs.ini

	# Create supervisor config
	cp configs/supervisor-cs.conf /etc/supervisor/conf.d/

	# Create nginx config
	rm -f /etc/nginx/sites-enabled/default
	cp configs/nginx_huaipeng_cs.conf /etc/nginx/sites-available/huaipeng_cs.conf
	ln -sf /etc/nginx/sites-available/huaipeng_cs.conf /etc/nginx/sites-enabled/huaipeng_cs.conf
}

function deploy_dataservice {
	setup_venv /srv/huaipeng/buildingdepot/

	cp -r DataService /srv/huaipeng/buildingdepot/

	cd /home/huaipeng/buildingdepot

	# copy uwsgi files
	cp configs/uwsgi_huaipeng_ds.ini /etc/uwsgi/apps-available/huaipeng_ds.ini

	# Create supervisor config
	cp configs/supervisor-ds.conf /etc/supervisor/conf.d/

	# Create nginx config
	rm -f /etc/nginx/sites-enabled/default
	cp configs/nginx_huaipeng_ds.conf /etc/nginx/sites-available/huaipeng_ds.conf
	ln -sf /etc/nginx/sites-available/huaipeng_ds.conf /etc/nginx/sites-enabled/huaipeng_ds.conf
}


function joint_deployment_fix {
	# Create join nginx config
	rm -f /etc/nginx/sites-enabled/default
	rm -f /etc/nginx/sites-enabled/huaipeng_ds.conf
	rm -f /etc/nginx/sites-available/huaipeng_ds.conf
	rm -f /etc/nginx/sites-enabled/huaipeng_cs.conf
	rm -f /etc/nginx/sites-available/huaipeng_cs.conf
	cd /home/huaipeng/buildingdepot
	cp configs/huaipeng_together.conf /etc/nginx/sites-available/huaipeng_together.conf
	ln -sf /etc/nginx/sites-available/huaipeng_together.conf /etc/nginx/sites-enabled/huaipeng_together.conf
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
	rm pip_packages.list
	cd -
}


if [ "$DEPLOY_CS" = true ]; then
	deploy_centralservice
fi

if [ "$DEPLOY_DS" = true ]; then
	deploy_dataservice
fi

service supervisor restart
supervisorctl reload
sleep 5
supervisorctl restart all

if [ "$DEPLOY_TOGETHER" = true ]; then
	joint_deployment_fix
	service nginx restart
fi

echo -e "\nInstallation Finished..\n"

