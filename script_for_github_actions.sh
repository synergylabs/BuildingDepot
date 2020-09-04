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

BD=/srv/buildingdepot/
pushd $(pwd)

cp configs/nginx.conf /etc/nginx/nginx.conf

mkdir -p /srv/buildingdepot
mkdir -p /var/log/buildingdepot/CentralService
mkdir -p /var/log/buildingdepot/DataService
mkdir -p /var/sockets


function setup_venv {
    cp pip_packages.list $1
    cd $1

    virtualenv ./venv
    source venv/bin/activate

    pip3 install --upgrade pip
    pip3 install --upgrade setuptools
    pip3 install --upgrade -r pip_packages.list

    pip3 install --upgrade uWSGI
    mkdir -p /etc/uwsgi/apps-available/

    deactivate
    cd -
}
# Deploy apps
function deploy_centralservice {
    setup_venv /srv/buildingdepot/

    #copy and untar new dataservice tarball
    cp -r buildingdepot/CentralService /srv/buildingdepot/
    cp -r buildingdepot/DataService /srv/buildingdepot/
    cp -r buildingdepot/CentralReplica /srv/buildingdepot/
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
    #Setting up SSL
    echo "Skipping SSL configuration..."
    #If user already has certificate
    cp configs/together.conf /etc/nginx/sites-available/together.conf
    ln -sf /etc/nginx/sites-available/together.conf /etc/nginx/sites-enabled/together.conf
}

function deploy_config {
    cp -r configs/ /srv/buildingdepot
    mkdir /var/sockets
}

function install_packages {
    apt-get install -y curl
    apt-get install -y apt-transport-https
    source /etc/lsb-release


    #Add keys for rabbitmq
    echo "deb https://dl.bintray.com/rabbitmq/debian ${DISTRIB_CODENAME} main" | sudo tee /etc/apt/sources.list.d/bintray.rabbitmq.list
    echo "deb https://dl.bintray.com/rabbitmq-erlang/debian ${DISTRIB_CODENAME} erlang" | sudo tee -a /etc/apt/sources.list.d/bintray.rabbitmq.list
    wget -O- https://www.rabbitmq.com/rabbitmq-release-signing-key.asc | sudo apt-key add -
    # Add keys to install influxdb
    curl -sL https://repos.influxdata.com/influxdb.key | sudo apt-key add -
    echo "deb https://repos.influxdata.com/${DISTRIB_ID,,} ${DISTRIB_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
    # Add keys to install mongodb
    wget -qO - https://www.mongodb.org/static/pgp/server-4.0.asc | sudo apt-key add -
    if [ $DISTRIB_CODENAME == "bionic" ]; then
        echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/${DISTRIB_ID,,} ${DISTRIB_CODENAME}/mongodb-org/4.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.0.list
    elif [ $DISTRIB_CODENAME == "xenial" ]; then
        echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/${DISTRIB_ID,,} ${DISTRIB_CODENAME}/mongodb-org/4.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.0.list
    elif [ $DISTRIB_CODENAME == "trusty" ]; then
        echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/${DISTRIB_ID,,} ${DISTRIB_CODENAME}/mongodb-org/4.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.0.list
    fi
    apt-get update -y
    apt-get install
    apt-get install -y python3-pip
    apt-get install -y mongodb-org=4.0.5 mongodb-org-server=4.0.5 mongodb-org-shell=4.0.5 mongodb-org-mongos=4.0.5 mongodb-org-tools=4.0.5
    apt-get install -y openssl python3-setuptools python3-dev build-essential software-properties-common
    apt-get install -y nginx
    apt-get install -y supervisor
    apt-get install -y redis-server
    pip3 install --upgrade virtualenv
    apt-get install -y wget
    apt-get install -y influxdb
    service influxdb start
    service mongod start
    apt-get install -y rabbitmq-server
    DEBIAN_FRONTEND=noninteractive apt-get install -y postfix
    apt-get install -y nodejs
    apt-get install -y npm
    sed -i -e 's/"inet_interfaces = all/"inet_interfaces = loopback-only"/g' /etc/postfix/main.cf
    service postfix restart
    systemctl enable mongod.service
}

function setup_gmail {
    echo "Please register an app in your Google API manager, generate an OAuth token and refresh token"
    echo "For more details refer to this url: https://github.com/google/gmail-oauth2-tools/wiki/OAuth2DotPyRunThrough"
    echo "Please enter your Gmail id"
    read email_id
    echo "Please enter your client id"
    read client_id
    echo "Please enter your client secret"
    read client_secret
    echo "Please enter access token"
    read access_token
    echo "Please enter refresh token"
    read refresh_token
    echo "EMAIL = 'GMAIL'" >> $BD/CentralService/cs_config
    echo "EMAIL_ID = '$email_id'" >> $BD/CentralService/cs_config
    echo "ACCESS_TOKEN = '$access_token'" >> $BD/CentralService/cs_config
    echo "REFRESH_TOKEN = '$refresh_token'" >> $BD/CentralService/cs_config
    echo "CLIENT_ID = '$client_id'" >> $BD/CentralService/cs_config
    echo "CLIENT_SECRET = '$client_secret'" >> $BD/CentralService/cs_config
}

function setup_email {
    echo "BuildingDepot requires a Mail Transfer Agent. Would you like to install one or use your gmail account?"
    echo "Note: If you use GMail, it is advised to create a new account for this purpose."
    echo "Installing an MTA..."
    sudo apt-get install -y mailutils
    sed -i -e 's/"inet_interfaces = all/"inet_interfaces = loopback-only"/g' /etc/postfix/main.cf
    service postfix restart
    echo "EMAIL = 'LOCAL'" >> $BD/CentralService/cs_config
    echo "EMAIL_ID = 'admin@buildingdepot.org'" >> $BD/CentralService/cs_config
}

function setup_packages {
    echo
    echo "Securing BD Packages"
    echo "--------------------"
    echo "Auto-generating credentials for packages (MongoDB,InfluxDB & Redis)..."
    ## Add MongoDB Admin user
    mongoUsername="user$(openssl rand -hex 16)"
    mongoPassword=$(openssl rand -hex 32)
    echo "MONGODB_USERNAME = '$mongoUsername'" >> $BD/CentralService/cs_config
    echo "MONGODB_PWD = '$mongoPassword'" >> $BD/CentralService/cs_config
    echo "MONGODB_USERNAME = '$mongoUsername'" >> $BD/DataService/ds_config
    echo "MONGODB_PWD = '$mongoPassword'" >> $BD/DataService/ds_config
    echo "    MONGODB_USERNAME = '$mongoUsername'" >> $BD/CentralReplica/config.py
    echo "    MONGODB_PWD = '$mongoPassword'" >> $BD/CentralReplica/config.py
    mongo --eval "db.getSiblingDB('admin').createUser({user:'$mongoUsername',pwd:'$mongoPassword',roles:['userAdminAnyDatabase','dbAdminAnyDatabase','readWriteAnyDatabase']})"
    # Enable MongoDB authorization
    echo "security:" >> /etc/mongod.conf
    echo "  authorization: \"enabled\"">> /etc/mongod.conf
    service mongod restart

    sleep 2

    ## Add InfluxDB Admin user
    influxUsername="user$(openssl rand -hex 16)"
    influxPassword=$(openssl rand -hex 32)
    echo "INFLUXDB_USERNAME = '$influxUsername'">> $BD/DataService/ds_config
    echo "INFLUXDB_PWD = '$influxPassword'">> $BD/DataService/ds_config
    sleep 1
    curl -d "q=CREATE USER $influxUsername WITH PASSWORD '$influxPassword' WITH ALL PRIVILEGES" -X POST http://localhost:8086/query
    sed -ir 's/# auth-enabled = false/auth-enabled = true/g' /etc/influxdb/influxdb.conf
    service influxdb restart

    sleep 2

    ## Add Redis Admin user
    redisPassword=$(openssl rand -hex 64)
    echo "REDIS_PWD = '$redisPassword'">> $BD/CentralService/cs_config
    echo "REDIS_PWD = '$redisPassword'">> $BD/DataService/ds_config
    echo "    REDIS_PWD = '$redisPassword'" >> $BD/CentralReplica/config.py
    sed -i -e '/#.* requirepass / s/.*/ requirepass  '$redisPassword'/' /etc/redis/redis.conf
    service redis restart

    echo
    echo "Auto-Generated User Credentials for BuildingDepot Packages [MongoDB,InfluxDB & Redis]"
    echo
}

deploy_config
install_packages
if [ "$DEPLOY_CS" = true ]; then
    deploy_centralservice
fi

if [ "$DEPLOY_DS" = true ]; then
    deploy_dataservice
fi

service mongod start
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

popd
setup_email


# Create Database on InfluxDB
curl -d "q=CREATE DATABASE buildingdepot" -X POST http://localhost:8086/query
setup_packages
/srv/buildingdepot/venv/bin/python setup_bd.py "test"
#
echo -e "\nInstallation Finished..\n"
supervisorctl restart all
