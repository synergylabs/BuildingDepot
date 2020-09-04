#!/bin/bash

set -e
set -o functrace
function failure() {
  local lineno=$1
  local msg=$2
  echo "Failed at $lineno: $msg"
}
trap 'failure ${LINENO} "$BASH_COMMAND"' ERR
sudo service supervisor stop || true

function get_os_ver() {
  if [ -f /etc/os-release ]; then
    # freedesktop.org and systemd
    . /etc/os-release
    OS=$NAME
    OS_VER=$VERSION_ID
  elif type lsb_release >/dev/null 2>&1; then
    # linuxbase.org
    OS=$(lsb_release -si)
    OS_VER=$(lsb_release -sr)
  elif [ -f /etc/lsb-release ]; then
    # For some versions of Debian/Ubuntu without lsb_release command
    . /etc/lsb-release
    OS=$DISTRIB_ID
    OS_VER=$DISTRIB_RELEASE
  elif [ -f /etc/debian_version ]; then
    # Older Debian/Ubuntu/etc.
    OS=Debian
    OS_VER=$(cat /etc/debian_version)
  elif [ -f /etc/SuSe-release ]; then
    # Older SuSE/etc.
    ...
  elif [ -f /etc/redhat-release ]; then
    # Older Red Hat, CentOS, etc.
    ...
  else
    # Fall back to uname, e.g. "Linux <version>", also works for BSD, etc.
    OS=$(uname -s)
    OS_VER=$(uname -r)
  fi
}
get_os_ver



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


mkdir -p /srv/buildingdepot
mkdir -p /var/log/buildingdepot/CentralService
mkdir -p /var/log/buildingdepot/DataService
mkdir -p /var/sockets || true

# Deploy apps
function deploy_centralservice {
    setup_venv /srv/buildingdepot/

    #copy and untar new dataservice tarball
    cp -r buildingdepot/CentralService /srv/buildingdepot/
    cp -r buildingdepot/DataService /srv/buildingdepot/
    cp -r buildingdepot/CentralReplica /srv/buildingdepot/
    #cp -r buildingdepot/OAuth2Server /srv/buildingdepot/
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
    ssl_conf_file='configs/bd_config.json'
    get_config_value 'cert_path'
    cert_path=$res
    get_config_value 'key_path'
    key_path=$res
    get_config_value 'domain'
    domain=$res
    sed -i "s|<cert_path>|$cert_path|g" /srv/buildingdepot/configs/together_ssl.conf
    sed -i "s|<key_path>|$key_path|g" /srv/buildingdepot/configs/together_ssl.conf
    sed -i "s|<domain>|$domain|g" /srv/buildingdepot/configs/together_ssl.conf
    cp configs/together_ssl.conf /etc/nginx/sites-available/together.conf
    ln -sf /etc/nginx/sites-available/together.conf /etc/nginx/sites-enabled/together.conf
}

function deploy_config {
    cp -r configs/ /srv/buildingdepot
    mkdir -p /var/sockets || true
}

function install_packages {
    apt-get install -y curl jq
    apt-get install -y apt-transport-https
    # Update rabbitmq key
    wget -O - "https://github.com/rabbitmq/signing-keys/releases/download/2.0/rabbitmq-release-signing-key.asc" | sudo apt-key add -
    echo 'deb http://www.rabbitmq.com/debian/ testing main' | sudo tee /etc/apt/sources.list.d/rabbitmq.list
    curl -sL https://repos.influxdata.com/influxdb.key | sudo apt-key add -
    source /etc/lsb-release
    echo "deb https://repos.influxdata.com/${DISTRIB_ID,,} ${DISTRIB_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
    sleep 10
    apt-get update
    apt-get install
    apt-get -y install python3-pip
    apt-get install -y mongodb
    apt-get install -y openssl python3-setuptools python3-dev build-essential
    if [ "$OS_VER" = "18.04" ];
    then
      apt-get install -y software-properties-common
    else
      apt-get install -y python3-software-properties
    fi
    apt-get install -y nginx
    apt-get install -y supervisor
    apt-get install -y redis-server
    pip3 install --upgrade virtualenv
    apt-get install -y wget
    sudo apt-get install -y influxdb
    sudo service influxdb start
    sleep 10
    sudo apt-get install rabbitmq-server
    #sed -i -e 's/"inet_interfaces = all/"inet_interfaces = loopback-only"/g' /etc/postfix/main.cf
    #service postfix restart
}

function setup_venv {
    cp -f pip_packages.list $1 || true
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

function get_config_value {
    prefix='.["'
    postfix='"]'
    res=$(jq $prefix$1$postfix configs/bd_config.json)
    res=${res:1:$(expr ${#res} - 2)}
}

function set_redis_credentials {
  echo $BD
  get_config_value 'redis_pwd'
  redis_pwd=$res
  echo "REDIS_PWD = '$redis_pwd'">> $BD/CentralService/cs_config
  echo "">> $BD/DataService/ds_config
  echo "REDIS_PWD = '$redis_pwd'">> $BD/DataService/ds_config
  echo "    REDIS_PWD = '$redis_pwd'" >> $BD/CentralReplica/config.py
  sed -i -e '/#.* requirepass / s/.*/ requirepass  '$redis_pwd'/' /etc/redis/redis.conf
  service redis restart
}

function set_influxdb_credentials {
  ## Add InfluxDB Admin user
  get_config_value 'influx_user'
  influx_user=$res
  get_config_value 'influx_pwd'
  influx_pwd=$res
  echo "INFLUXDB_USERNAME = '$influx_user'">> $BD/DataService/ds_config
  echo "INFLUXDB_PWD = '$influx_pwd'">> $BD/DataService/ds_config
  sleep 1
  curl -d "q=CREATE USER $influx_user WITH PASSWORD '$influx_pwd' WITH ALL PRIVILEGES" -X POST http://localhost:8086/query
  sed -ir 's/# auth-enabled = false/auth-enabled = true/g' /etc/influxdb/influxdb.conf
        service influxdb restart
}

function set_mongodb_credentials {
  get_config_value 'mongo_user'
  mongo_user=$res
  get_config_value 'mongo_pwd'
  mongo_pwd=$res
  echo "MONGODB_USERNAME = '$mongo_user'" >> $BD/CentralService/cs_config
  echo "MONGODB_PWD = '$mongo_pwd'" >> $BD/CentralService/cs_config
  echo "MONGODB_USERNAME = '$mongo_user'" >> $BD/DataService/ds_config
  echo "MONGODB_PWD = '$mongo_pwd'" >> $BD/DataService/ds_config
  echo "    MONGODB_USERNAME = '$mongo_user'" >> $BD/CentralReplica/config.py
  echo "    MONGODB_PWD = '$mongo_pwd'" >> $BD/CentralReplica/config.py
  mongo --eval "db.getSiblingDB('admin').createUser({user:'$mongo_user',pwd:'$mongo_pwd',roles:['userAdminAnyDatabase','dbAdminAnyDatabase','readWriteAnyDatabase']})" || true
  # Enable MongoDB authorization
  lastline=$(cat /etc/mongodb.conf | tail -1)
  auth_opt="auth = true"
  if ["$lastline" != "$auth_opt"]; then
      echo $auth_opt >> /etc/mongodb.conf
  fi
  #echo "security:" >> /etc/mongod.conf
  #echo "  authorization: \"enabled\"">> /etc/mongod.conf
  service mongodb restart


}


function set_credentials {
  set_redis_credentials
  set_influxdb_credentials
  set_mongodb_credentials
}


function setup_gmail {
    get_config_value 'client_id'
    client_id=$res
    get_config_value 'client_secret'
    client_secret=$res
    get_config_value 'email'
    email_id=$res
    get_config_value 'refresh_token'
    refresh_token=$res
    get_config_value 'access_token'
    access_token=$res
    echo "EMAIL = 'GMAIL'" >> $BD/CentralService/cs_config
    echo "EMAIL_ID = '$email_id'" >> $BD/CentralService/cs_config
    echo "ACCESS_TOKEN = '$access_token'" >> $BD/CentralService/cs_config
    echo "REFRESH_TOKEN = '$refresh_token'" >> $BD/CentralService/cs_config
    echo "CLIENT_ID = '$client_id'" >> $BD/CentralService/cs_config
    echo "CLIENT_SECRET = '$client_secret'" >> $BD/CentralService/cs_config
}

deploy_config
install_packages
cp configs/nginx.conf /etc/nginx/nginx.conf
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
set_credentials

if [ "$DEPLOY_TOGETHER" = true ]; then
    joint_deployment_fix
    service nginx restart
fi

rm -rf configs

popd
setup_gmail

#curl -G http://localhost:8086/query --data-urlencode "q=CREATE DATABASE buildingdepot" #TODO: Implement this with admin account
echo -e "\nInstallation Finished..\n"
/srv/buildingdepot/venv/bin/python setup_bd.py "bd_install"
echo -e "Created a super user with following credentials. Please login and change password immediately \n user id : admin@buildingdepot.org \n password: admin"

supervisorctl restart cs
