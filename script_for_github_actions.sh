#!/bin/bash

DEPLOY_TOGETHER=true
DEPLOY_CS=true
DEPLOY_DS=true

################################################################################
# Check and make sure we are running as root or (?)
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

function setup_venv() {
  cp pip_packages.list $1
  cd $1

  virtualenv ./venv
  source venv/bin/activate

  pip3 install --upgrade pip
  pip3 install --upgrade setuptools
  if [ $DISTRIB_CODENAME == "bionic" ]; then
    pip3 install "Flask==2.0.3"
  else
    pip3 install "Flask==2.1.3"
  fi
  pip3 install --upgrade -r pip_packages.list
  pip3 install "firebase-admin"
  pip3 install --upgrade uWSGI
  mkdir -p /etc/uwsgi/apps-available/

  deactivate
  cd -
}
# Deploy apps
function deploy_centralservice() {
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

function deploy_dataservice() {
  setup_venv /srv/buildingdepot/

  cd /srv/buildingdepot

  # copy uwsgi files
  cp configs/uwsgi_ds.ini /etc/uwsgi/apps-available/ds.ini

  # Create supervisor config
  cp configs/supervisor-ds.conf /etc/supervisor/conf.d/

  # Create nginx config
  rm -f /etc/nginx/sites-enabled/default
}

function joint_deployment_fix() {
  # Create join nginx config
  rm -f /etc/nginx/sites-enabled/default
  cd /srv/buildingdepot
  #Setting up SSL
  echo "Skipping SSL configuration..."
  #If user already has certificate
  cp configs/together.conf /etc/nginx/sites-available/together.conf
  ln -sf /etc/nginx/sites-available/together.conf /etc/nginx/sites-enabled/together.conf
}

function deploy_config() {
  cp -r configs/ /srv/buildingdepot
  mkdir /var/sockets
}

function install_packages() {
  apt-get install -y curl
  apt-get install -y apt-transport-https
  apt-get install -y gnupg
  source /etc/lsb-release

  # Add keys for Rabbitmq
  curl -s https://packagecloud.io/install/repositories/rabbitmq/rabbitmq-server/script.deb.sh | bash
  # Adds Launchpad PPA that provides modern Erlang releases
  curl -1sLf "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xf77f1eda57ebb1cc" | sudo gpg --dearmor | sudo tee /usr/share/keyrings/net.launchpad.ppa.rabbitmq.erlang.gpg > /dev/null
  echo "deb [ signed-by=/usr/share/keyrings/net.launchpad.ppa.rabbitmq.erlang.gpg ] http://ppa.launchpad.net/rabbitmq/rabbitmq-erlang/ubuntu ${DISTRIB_CODENAME} main" | tee /etc/apt/sources.list.d/rabbitmq-erlang.list
  echo "deb-src [ signed-by=/usr/share/keyrings/net.launchpad.ppa.rabbitmq.erlang.gpg ] http://ppa.launchpad.net/rabbitmq/rabbitmq-erlang/ubuntu ${DISTRIB_CODENAME} main" | tee -a /etc/apt/sources.list.d/rabbitmq-erlang.list

   # Add keys to install influxdb
  curl -s https://repos.influxdata.com/influxdata-archive_compat.key > influxdata-archive_compat.key
  echo '393e8779c89ac8d958f81f942f9ad7fb82a25e133faddaf92e15b16e6ac9ce4c influxdata-archive_compat.key' | sha256sum -c && cat influxdata-archive_compat.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg > /dev/null
  echo 'deb [ signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg ] https://repos.influxdata.com/debian stable main' | sudo tee /etc/apt/sources.list.d/influxdata.list

  # Add keys to install mongodb
  if [ $DISTRIB_CODENAME == "bionic" ]; then
    curl -fsSL https://pgp.mongodb.com/server-6.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg --dearmor
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] https://repo.mongodb.org/apt/ubuntu ${DISTRIB_CODENAME}/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
  else
    curl -fsSL https://pgp.mongodb.com/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu ${DISTRIB_CODENAME}/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
  fi

  apt-get update -y
  apt-get install
  apt-get install -y python3-pip

  if [ $DISTRIB_CODENAME == "bionic" ]; then
    apt-get install -y mongodb-org=6.0.10 mongodb-org-database=6.0.10 mongodb-org-server=6.0.10 mongodb-org-mongos=6.0.10 mongodb-org-tools=6.0.10
  else
    apt-get install -y mongodb-org
  fi

  apt-get install -y openssl python3-setuptools python3-dev build-essential software-properties-common
  apt-get install -y nginx
  apt-get install -y supervisor
  apt-get install -y redis-server
  pip3 install --upgrade virtualenv
  apt-get install -y wget
  apt-get install -y influxdb
  service influxdb start
  systemctl start mongod
  systemctl enable mongod.service
  apt-get install -y erlang-base \
    erlang-asn1 erlang-crypto erlang-eldap erlang-ftp erlang-inets \
    erlang-mnesia erlang-os-mon erlang-parsetools erlang-public-key \
    erlang-runtime-tools erlang-snmp erlang-ssl \
    erlang-syntax-tools erlang-tftp erlang-tools erlang-xmerl
  apt-get install -y rabbitmq-server --fix-missing
  DEBIAN_FRONTEND=noninteractive apt-get install -y postfix
  curl -fsSL https://deb.nodesource.com/setup_lts.x | -E bash -
  apt-get install -y nodejs
  apt-get install -y npm
  sed -i -e 's/"inet_interfaces = all/"inet_interfaces = loopback-only"/g' /etc/postfix/main.cf
  service postfix restart
}

function setup_gmail() {
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
  echo "EMAIL = 'GMAIL'" >>$BD/CentralService/cs_config
  echo "EMAIL_ID = '$email_id'" >>$BD/CentralService/cs_config
  echo "ACCESS_TOKEN = '$access_token'" >>$BD/CentralService/cs_config
  echo "REFRESH_TOKEN = '$refresh_token'" >>$BD/CentralService/cs_config
  echo "CLIENT_ID = '$client_id'" >>$BD/CentralService/cs_config
  echo "CLIENT_SECRET = '$client_secret'" >>$BD/CentralService/cs_config
}

function setup_email() {
  echo "BuildingDepot requires a Mail Transfer Agent. Would you like to install one or use your gmail account?"
  echo "Note: If you use GMail, it is advised to create a new account for this purpose."
  echo "Installing an MTA..."
  apt-get install -y mailutils
  sed -i -e 's/"inet_interfaces = all/"inet_interfaces = loopback-only"/g' /etc/postfix/main.cf
  service postfix restart
  echo "EMAIL = 'LOCAL'" >>$BD/CentralService/cs_config
  echo "EMAIL_ID = 'admin@buildingdepot.org'" >>$BD/CentralService/cs_config
}

function setup_packages() {
  echo
  echo "Securing BD Packages"
  echo "--------------------"
  echo "Auto-generating credentials for packages (MongoDB,InfluxDB & Redis)..."
  ## Add MongoDB Admin user
  mongoUsername="user$(openssl rand -hex 16)"
  mongoPassword=$(openssl rand -hex 32)
  echo "MONGODB_USERNAME = '$mongoUsername'" >>$BD/CentralService/cs_config
  echo "MONGODB_PWD = '$mongoPassword'" >>$BD/CentralService/cs_config
  echo "MONGODB_USERNAME = '$mongoUsername'" >>$BD/DataService/ds_config
  echo "MONGODB_PWD = '$mongoPassword'" >>$BD/DataService/ds_config
  echo "    MONGODB_USERNAME = '$mongoUsername'" >>$BD/CentralReplica/config.py
  echo "    MONGODB_PWD = '$mongoPassword'" >>$BD/CentralReplica/config.py

  mongosh --eval "db.getSiblingDB('admin').createUser({user:'$mongoUsername',pwd:'$mongoPassword',roles:['userAdminAnyDatabase','dbAdminAnyDatabase','readWriteAnyDatabase']})"

 # Enable MongoDB authorization
  echo "security:" >>/etc/mongod.conf
  echo "  authorization: \"enabled\"" >>/etc/mongod.conf
  service mongod restart

  sleep 2

  ## Add InfluxDB Admin user
  influxUsername="user$(openssl rand -hex 16)"
  influxPassword=$(openssl rand -hex 32)
  echo "INFLUXDB_USERNAME = '$influxUsername'" >>$BD/DataService/ds_config
  echo "INFLUXDB_PWD = '$influxPassword'" >>$BD/DataService/ds_config
  sleep 1
  curl -d "q=CREATE USER $influxUsername WITH PASSWORD '$influxPassword' WITH ALL PRIVILEGES" -X POST http://localhost:8086/query
  sed -ir 's/# auth-enabled = false/auth-enabled = true/g' /etc/influxdb/influxdb.conf
  service influxdb restart

  sleep 2

  ## Add Redis Admin user
  redisPassword=$(openssl rand -hex 64)
  echo "REDIS_PWD = '$redisPassword'" >>$BD/CentralService/cs_config
  echo "REDIS_PWD = '$redisPassword'" >>$BD/DataService/ds_config
  echo "    REDIS_PWD = '$redisPassword'" >>$BD/CentralReplica/config.py
  sed -i -e '/#.* requirepass / s/.*/ requirepass  '$redisPassword'/' /etc/redis/redis.conf
  service redis restart

  sleep 2

  ## Add RabbitMQ Admin user
  rabbitmqUsername="user$(openssl rand -hex 16)"
  rabbitmqPassword=$(openssl rand -hex 32)
  rabbitmqUsername_endUser="user$(openssl rand -hex 16)"
  rabbitmqPassword_endUser=$(openssl rand -hex 32)
  echo "RABBITMQ_ADMIN_USERNAME = '$rabbitmqUsername'" >>$BD/DataService/ds_config
  echo "RABBITMQ_ADMIN_PWD = '$rabbitmqPassword'" >>$BD/DataService/ds_config
  echo "RABBITMQ_ENDUSER_USERNAME = '$rabbitmqUsername_endUser'" >>$BD/DataService/ds_config
  echo "RABBITMQ_ENDUSER_PWD = '$rabbitmqPassword_endUser'" >>$BD/DataService/ds_config
  # Create a Admin user.
  rabbitmqctl add_user "$rabbitmqUsername" "$rabbitmqPassword"
  # Add Administrative Rights
  rabbitmqctl set_user_tags "$rabbitmqUsername" administrator
  # Grant necessary permissions
  rabbitmqctl set_permissions -p / "$rabbitmqUsername" ".*" ".*" ".*"
  # Create a End User.
  rabbitmqctl add_user "$rabbitmqUsername_endUser" "$rabbitmqPassword_endUser"
  # Add Permissions
  rabbitmqctl set_user_tags "$rabbitmqUsername_endUser"
  # Grant necessary permissions
  rabbitmqctl set_permissions -p / "$rabbitmqUsername_endUser" "" "" ".*"
  echo "BuildingDepot uses RabbitMQ Queues for Publishing  and Subscribing to Sensor data. "
  echo "Some web front-end use RabbitMQ Queues use rabbitmq_web_stomp plugin"
  echo "Enter Y to install rabbitmq_web_stomp plugin: "
  rabbitmq-plugins enable rabbitmq_web_stomp

  sleep 1

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
cat /srv/buildingdepot/CentralService/cs_config
cat /srv/buildingdepot/DataService/ds_config
tail -500 /var/log/buildingdepot/CentralService/uwsgi-app.log
tail -500 /var/log/buildingdepot/DataService/uwsgi-app.log