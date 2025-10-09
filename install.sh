#!/usr/bin/env bash
set -euox pipefail

################################################################################
# Check and make sure we are running as root or sudo (?)
################################################################################
if [[ $UID -ne 0 ]]; then
  echo -e "\n$0 must be run as root. Most functions require super-user priviledges!\n"
  exit 1
fi

BD=/srv/buildingdepot
pushd $(pwd)

mkdir -p /etc/nginx
mkdir -p /var/log/buildingdepot/CentralService
mkdir -p /var/log/buildingdepot/DataService
mkdir -p /var/sockets

# Deploy apps
function deploy_services() {
  uv sync

  #copy and untar new dataservice tarball
  ln -s $(pwd) $BD
  cd $BD

  # Create systemd config for central replica
  cp configs/bd-replica.service /etc/systemd/system/
  systemctl enable bd-replica.service

  # Create systemd config for central service
  cp configs/bd-central.service /etc/systemd/system/
  systemctl enable bd-central.service

  # Create systemd config for data service
  cp configs/bd-data.service /etc/systemd/system/
  systemctl enable bd-data.service

  # Create nginx config
  rm -f /etc/nginx/sites-enabled/default

  #Setting up SSL
  echo "Do you have a SSL certificate and key that you would like to use? Please enter [y/n]"
  read response

  #If user already has certificate
  if [ "$response" == "Y" ] || [ "$response" == "y" ]; then
    echo "Please enter the path to the CA certificate (fullchain.pem):"
    read ca_cert_path
    sed -i "s|<cert_path>|$ca_cert_path|g" configs/together_ssl.conf
    echo "Please enter the path to the server certificate (cert.pem):"
    read cert_path
    echo "Please enter the path to the server key (privkey.pem):"
    read key_path
    sed -i "s|<key_path>|$key_path|g" configs/together_ssl.conf
    echo "Please enter the ip address or the domain name of this installation"
    read domain
    sed -i "s|<domain>|$domain|g" configs/together_ssl.conf
    cp configs/together_ssl.conf /etc/nginx/sites-available/together.conf

    #Setting up SSL for packages
    echo "Would you like to use these SSL certificates for BD packages (RabbitMQ)? [y/n]"
    read response_packages
    if [ "$response_packages" == "Y" ] || [ "$response_packages" == "y" ]; then
      mkdir -p /etc/rabbitmq/ssl
      cp -rL --remove-destination "$ca_cert_path" /etc/rabbitmq/ssl/fullchain.pem
      cp -rL --remove-destination "$cert_path" /etc/rabbitmq/ssl/cert.pem
      cp -rL --remove-destination "$key_path" /etc/rabbitmq/ssl/privkey.pem
      chmod -R 555 /etc/rabbitmq/ssl/
      cp configs/rabbitmq.conf /etc/rabbitmq/rabbitmq.conf
      service rabbitmq-server restart

      #Setting up certbot post hook
      echo "Have you installed certbot to automatically renew the SSL certificates? [y/n]"
      read response_certbot

      if [ "$response_certbot" == "Y" ] || [ "$response_certbot" == "y" ]; then
        sed -i "s|<cert_path>|$ca_cert_path|g" configs/certbot_post_hook.sh
        sed -i "s|<server_cert_path>|$cert_path|g" configs/certbot_post_hook.sh
        sed -i "s|<privkey_path>|$key_path|g" configs/certbot_post_hook.sh
        cp configs/certbot_post_hook.sh /etc/letsencrypt/renewal-hooks/deploy/
        chmod +x /etc/letsencrypt/renewal-hooks/deploy/certbot_post_hook.sh
      fi
    fi
  else
    cp configs/together.conf /etc/nginx/sites-available/together.conf
  fi
  ln -sf /etc/nginx/sites-available/together.conf /etc/nginx/sites-enabled/together.conf
}

function install_packages() {
  apt-get install -y curl wget apt-transport-https gnupg openssl
  source /etc/lsb-release

  # Add keys to install influxdb
  curl -s https://repos.influxdata.com/influxdata-archive_compat.key > influxdata-archive_compat.key
  echo '393e8779c89ac8d958f81f942f9ad7fb82a25e133faddaf92e15b16e6ac9ce4c influxdata-archive_compat.key' | sha256sum -c && cat influxdata-archive_compat.key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg > /dev/null
  echo 'deb [ signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg ] https://repos.influxdata.com/debian stable main' | tee /etc/apt/sources.list.d/influxdata.list

  ## RabbitMQ's main signing key
  curl -1sLf "https://keys.openpgp.org/vks/v1/by-fingerprint/0A9AF2115F4687BD29803A206B73A36E6026DFCA" | gpg --dearmor | tee /usr/share/keyrings/com.rabbitmq.team.gpg > /dev/null
  ## Community mirror of Cloudsmith: modern Erlang repository
  curl -1sLf https://github.com/rabbitmq/signing-keys/releases/download/3.0/cloudsmith.rabbitmq-erlang.E495BB49CC4BBE5B.key | gpg --dearmor | tee /usr/share/keyrings/rabbitmq.E495BB49CC4BBE5B.gpg > /dev/null
  ## Community mirror of Cloudsmith: RabbitMQ repository
  curl -1sLf https://github.com/rabbitmq/signing-keys/releases/download/3.0/cloudsmith.rabbitmq-server.9F4587F226208342.key | gpg --dearmor | tee /usr/share/keyrings/rabbitmq.9F4587F226208342.gpg > /dev/null

  ## Add apt repositories maintained by Team RabbitMQ
  tee /etc/apt/sources.list.d/rabbitmq.list <<EOF
## Provides modern Erlang/OTP releases
##
deb [arch=amd64 signed-by=/usr/share/keyrings/rabbitmq.E495BB49CC4BBE5B.gpg] https://ppa1.rabbitmq.com/rabbitmq/rabbitmq-erlang/deb/ubuntu ${DISTRIB_CODENAME} main
deb-src [signed-by=/usr/share/keyrings/rabbitmq.E495BB49CC4BBE5B.gpg] https://ppa1.rabbitmq.com/rabbitmq/rabbitmq-erlang/deb/ubuntu ${DISTRIB_CODENAME} main

# another mirror for redundancy
deb [arch=amd64 signed-by=/usr/share/keyrings/rabbitmq.E495BB49CC4BBE5B.gpg] https://ppa2.rabbitmq.com/rabbitmq/rabbitmq-erlang/deb/ubuntu ${DISTRIB_CODENAME} main
deb-src [signed-by=/usr/share/keyrings/rabbitmq.E495BB49CC4BBE5B.gpg] https://ppa2.rabbitmq.com/rabbitmq/rabbitmq-erlang/deb/ubuntu ${DISTRIB_CODENAME} main

## Provides RabbitMQ
##
deb [arch=amd64 signed-by=/usr/share/keyrings/rabbitmq.9F4587F226208342.gpg] https://ppa1.rabbitmq.com/rabbitmq/rabbitmq-server/deb/ubuntu ${DISTRIB_CODENAME} main
deb-src [signed-by=/usr/share/keyrings/rabbitmq.9F4587F226208342.gpg] https://ppa1.rabbitmq.com/rabbitmq/rabbitmq-server/deb/ubuntu ${DISTRIB_CODENAME} main

# another mirror for redundancy
deb [arch=amd64 signed-by=/usr/share/keyrings/rabbitmq.9F4587F226208342.gpg] https://ppa2.rabbitmq.com/rabbitmq/rabbitmq-server/deb/ubuntu ${DISTRIB_CODENAME} main
deb-src [signed-by=/usr/share/keyrings/rabbitmq.9F4587F226208342.gpg] https://ppa2.rabbitmq.com/rabbitmq/rabbitmq-server/deb/ubuntu ${DISTRIB_CODENAME} main
EOF

  # Add keys to install mongodb
  curl -fsSL https://pgp.mongodb.com/server-7.0.asc | gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
  echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu ${DISTRIB_CODENAME}/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list

  apt-get update -y
  apt-get install -y \
      python3-pip python3-setuptools python3-dev build-essential software-properties-common \
      nginx \
      redis-server \
      mongodb-org \
      influxdb \
      erlang-base \
      erlang-asn1 erlang-crypto erlang-eldap erlang-ftp erlang-inets \
      erlang-mnesia erlang-os-mon erlang-parsetools erlang-public-key \
      erlang-runtime-tools erlang-snmp erlang-ssl \
      erlang-syntax-tools erlang-tftp erlang-tools erlang-xmerl \
      rabbitmq-server
  systemctl enable influxdb
  systemctl start influxdb
  systemctl enable mongod
  systemctl start mongod
  systemctl enable mongod
  systemctl start mongod
  snap install node --channel=22 --classic
  snap install astral-uv --classic
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
  echo "Enter Y to install an MTA and N to use your GMail account."
  read response
  if [ "$response" == "Y" ] || [ "$response" == "y" ]; then
    apt-get install -y mailutils
    sed -i -e 's/"inet_interfaces = all/"inet_interfaces = loopback-only"/g' /etc/postfix/main.cf
    service postfix restart
    while true; do
      echo "Please enter email address to send test mail:"
      read email_id
      n=$(od -An -N2 -i /dev/random)
      echo $n | mail -s "Test email from BuildingDepot" $email_id
      echo "Please enter the number you received in the mail"
      read input
      if [ $input == $n ]; then
        echo "EMAIL = 'LOCAL'" >>$BD/CentralService/cs_config
        echo "EMAIL_ID = 'admin@buildingdepot.org'" >>$BD/CentralService/cs_config
        break
      else
        echo "Verification failed. Enter R to retry, Y to use GMail"
        read response
        if [ "$response" == "R" ] || [ "$response" == "r" ]; then
          continue
        elif [ "$response" == 'Y' ] || [ "$response" == 'y' ]; then
          setup_gmail
          break
        else
          echo "Invalid input! Exiting!"
          exit
        fi
      fi
    done
  else
    setup_gmail
  fi
}

function setup_notifications() {
  echo "BuildingDepot uses notifications to alert users or systems of events in real-time. By default, "
  echo "BuildingDepot uses RabbitMQ to deliver messages and we also supports Google Firebase Cloud Messaging (FCM), "
  echo "which allows BuildingDepot to send push notifications to mobile users."
  echo "Enter Y to select Google FCM and N to select RabbitMQ: "
  read response
  if [ "$response" == "Y" ] || [ "$response" == "y" ]; then
    echo "Please provide the absolute path of where your Google Service Account JSON file is, which contains the keys for your FCM project."
    read response
    if [ ! -z "$response" ]; then
      echo "NOTIFICATION_TYPE = 'FIREBASE'" >>$BD/CentralService/cs_config
      echo "FIREBASE_CREDENTIALS = '$response'" >>$BD/CentralService/cs_config
    fi
  elif [ "$response" == "N" ] || [ "$response" == "n" ]; then
    echo "NOTIFICATION_TYPE = 'RabbitMQ'" >>$BD/CentralService/cs_config
  fi
}

function setup_packages() {

  echo
  echo "Securing BD Packages"
  echo "--------------------"
  echo "Enter Y to auto-generate credentials for packages (MongoDB,InfluxDB & Redis). Credentials are stored in cs_config file (or) Enter N to input individual package credentials"
  read response
  if [ "$response" == "Y" ] || [ "$response" == "y" ]; then
    ## Add MongoDB Admin user

    if [ -f "$BD/CentralService/cs_config" ] && [ -f "/etc/mongod.conf" ] && grep -q "authorization: \"enabled\"" /etc/mongod.conf; then
        echo "MongoDB is already set up. Please remove MongoDB by running `sudo rm -rf /var/lib/mongodb/* /etc/mongod.conf /etc/influxdb && sudo apt remove --purge --autoremove mongodb-org redis-server rabbitmq-server influxdb` and run installation script again."
        exit 1
    else
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

    fi

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

    echo "BuildingDepot uses RabbitMQ Queues for Publishing and Subscribing to Sensor data. "
    echo "Some web front-end use RabbitMQ Queues use rabbitmq_web_stomp plugin"
    echo "Enter Y to install rabbitmq_web_stomp plugin: "
    read response
    if [ "$response" == "Y" ] || [ "$response" == "y" ]; then
      rabbitmq-plugins enable rabbitmq_web_stomp
    fi

    sleep 1

    echo
    echo "Auto-Generated User Credentials for BuildingDepot Packages [MongoDB,InfluxDB & Redis]"
    echo

  elif [ "$response" == 'N' ] || [ "$response" == 'n' ]; then
    ## Add MongoDB Admin user
    echo "Enter MongoDB Username: "
    read mongoUsername
    echo "Enter MongoDB Password: "
    read -s mongoPassword
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
    echo
    echo "Enter InfluxDB Username: "
    read influxUsername
    echo "Enter InfluxDB Password: "
    read -s influxPassword
    echo "INFLUXDB_USERNAME = '$influxUsername'" >>$BD/DataService/ds_config
    echo "INFLUXDB_PWD = '$influxPassword'" >>$BD/DataService/ds_config
    sleep 1
    curl -d "q=CREATE USER $influxUsername WITH PASSWORD '$influxPassword' WITH ALL PRIVILEGES" -X POST http://localhost:8086/query
    sed -ir 's/# auth-enabled = false/auth-enabled = true/g' /etc/influxdb/influxdb.conf
    service influxdb restart

    sleep 2

    ## Add Redis Admin user
    echo
    echo "Enter Redis Username: "
    read redisUsername
    echo "Enter Redis Password: "
    read -s redisPassword
    echo "REDIS_PWD = '$redisPassword'" >>$BD/CentralService/cs_config
    echo "REDIS_PWD = '$redisPassword'" >>$BD/DataService/ds_config
    echo "    REDIS_PWD = '$redisPassword'" >>$BD/CentralReplica/config.py
    sed -i -e '/#.* requirepass / s/.*/ requirepass  '$redisPassword'/' /etc/redis/redis.conf
    service redis restart

    sleep 2

    ## Add RabbitMQ Admin user
    echo
    echo "Enter RabbitMQ Admin Username: "
    read rabbitmqUsername
    echo "Enter RabbitMQ Admin Password: "
    read -s rabbitmqPassword
    echo "Enter RabbitMQ EndUser Username: "
    read rabbitmqUsername_endUser
    echo "Enter RabbitMQ EndUser Password: "
    read -s rabbitmqPassword_endUser

    #Create a new user.
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

    echo "RABBITMQ_ADMIN_USERNAME = '$rabbitmqUsername'" >>$BD/DataService/ds_config
    echo "RABBITMQ_ADMIN_PWD = '$rabbitmqPassword'" >>$BD/DataService/ds_config
    echo "RABBITMQ_ENDUSER_USERNAME = '$rabbitmqUsername_endUser'" >>$BD/DataService/ds_config
    echo "RABBITMQ_ENDUSER_PWD = '$rabbitmqPassword_endUser'" >>$BD/DataService/ds_config

    echo "BuildingDepot uses RabbitMQ Queues for Publishing and Subscribing to Sensor data. "
    echo "Some web front-end use RabbitMQ Queues use rabbitmq_web_stomp plugin"
    echo "Enter Y to install rabbitmq_web_stomp plugin: "
    read response
    if [ "$response" == "Y" ] || [ "$response" == "y" ]; then
      rabbitmq-plugins enable rabbitmq_web_stomp
    fi

    sleep 1

    echo
    echo "Saved User Credentials for BuildingDepot Packages"
    echo

  else
    echo
    echo "Invalid option please Try again."
    setup_packages
  fi

}

install_packages
deploy_services

service mongod restart
service influxdb restart

popd
setup_email
setup_notifications

# Create Database on InfluxDB
curl -d "q=CREATE DATABASE buildingdepot" -X POST http://localhost:8086/query
setup_packages
uv run python3 setup_bd.py "install"
#
echo -e "\nInstallation Finished..\n"

systemctl stop bd-central
systemctl stop bd-replica
systemctl stop bd-data
systemctl start bd-replica
systemctl start bd-central
systemctl start bd-data
