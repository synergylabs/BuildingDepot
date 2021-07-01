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

    pip install --upgrade pip
    pip install --upgrade setuptools
    pip install --upgrade -r pip_packages.list

    pip install --upgrade uWSGI
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
    #Setting up SSL
    echo "Do you have a SSL certificate and key that you would like to use? Please enter [y/n]"
    read response
    #If user already has certificate
    if [ "$response" == "Y" ] || [ "$response" == "y" ]; then
            echo "Please enter the path to the certificate:"
            read cert_path
            sed -i "s|<cert_path>|$cert_path|g" /srv/buildingdepot/configs/together_ssl.conf
            echo "Please enter the path to the key:"
            read key_path
            sed -i "s|<key_path>|$key_path|g" /srv/buildingdepot/configs/together_ssl.conf
        echo "Please enter the ip address or the domain name of this installation"
            read domain
            sed -i "s|<domain>|$domain|g" /srv/buildingdepot/configs/together_ssl.conf
        cp configs/together_ssl.conf /etc/nginx/sites-available/together.conf
    else
        cp configs/together.conf /etc/nginx/sites-available/together.conf
    fi
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

    # Add keys for Rabbitmq
    curl -s https://packagecloud.io/install/repositories/rabbitmq/rabbitmq-server/script.deb.sh | bash
    # Adds Launchpad PPA that provides modern Erlang releases
    sudo apt-key adv --keyserver "keyserver.ubuntu.com" --recv-keys "F77F1EDA57EBB1CC"
    echo "deb http://ppa.launchpad.net/rabbitmq/rabbitmq-erlang/ubuntu ${DISTRIB_CODENAME} main" | tee /etc/apt/sources.list.d/rabbitmq-erlang.list
    echo "deb-src http://ppa.launchpad.net/rabbitmq/rabbitmq-erlang/ubuntu ${DISTRIB_CODENAME} main" | tee -a /etc/apt/sources.list.d/rabbitmq-erlang.list

    # Add keys to install influxdb
    curl -sL https://repos.influxdata.com/influxdb.key | sudo apt-key add -
    echo "deb https://repos.influxdata.com/${DISTRIB_ID,,} ${DISTRIB_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/influxdb.list

    # Add keys to install mongodb
    wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -
    if [ $DISTRIB_CODENAME == "focal" ]; then
        echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu ${DISTRIB_CODENAME}/mongodb-org/4.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list
    elif [ $DISTRIB_CODENAME == "bionic" ]; then
        echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu ${DISTRIB_CODENAME}/mongodb-org/4.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list
    elif [ $DISTRIB_CODENAME == "xenial" ]; then
        echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu ${DISTRIB_CODENAME}/mongodb-org/4.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list
    elif [ $DISTRIB_CODENAME == "trusty" ]; then
        wget -qO - https://www.mongodb.org/static/pgp/server-4.0.asc | sudo apt-key add -
        echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/${DISTRIB_ID,,} ${DISTRIB_CODENAME}/mongodb-org/4.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.0.list
    fi

    apt-get update -y
    apt-get install
    apt-get -y install python-pip

    if [ $DISTRIB_CODENAME == "trusty" ]; then
      apt-get install -y mongodb-org=4.0.25 mongodb-org-server=4.0.25 mongodb-org-shell=4.0.25 mongodb-org-mongos=4.0.25 mongodb-org-tools=4.0.25
    else
      apt-get install -y mongodb-org=4.4.6 mongodb-org-server=4.4.6 mongodb-org-shell=4.4.6 mongodb-org-mongos=4.4.6 mongodb-org-tools=4.4.6
    fi

    apt-get install -y openssl python-setuptools python-dev build-essential software-properties-common
    apt-get install -y nginx
    apt-get install -y supervisor
    apt-get install -y redis-server
    pip install --upgrade virtualenv
    apt-get install -y wget
    apt-get install -y influxdb
    service influxdb start
    service mongod start
    apt-get install -y erlang-base \
                  erlang-asn1 erlang-crypto erlang-eldap erlang-ftp erlang-inets \
                  erlang-mnesia erlang-os-mon erlang-parsetools erlang-public-key \
                  erlang-runtime-tools erlang-snmp erlang-ssl \
                  erlang-syntax-tools erlang-tftp erlang-tools erlang-xmerl
    apt-get install -y rabbitmq-server
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
    echo "Enter Y to install an MTA and N to use your GMail account."
    read response
    if [ "$response" == "Y" ] || [ "$response" == "y" ]; then
        sudo apt-get install -y mailutils
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
                echo "EMAIL = 'LOCAL'" >> $BD/CentralService/cs_config
		echo "EMAIL_ID = 'admin@buildingdepot.org'" >> $BD/CentralService/cs_config
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

function setup_notifications {
    echo "BuildingDepot uses notifications to alert users or systems of events in real-time. By default, "
    echo "BuildingDepot uses RabbitMQ to deliver messages and we also supports Google Firebase Cloud Messaging (FCM), "
    echo "which allows BuildingDepot to send push notifications to mobile users."
    echo "Enter Y to select Google FCM and N to select RabbitMQ: "
    read response
    if [ "$response" == "Y" ] || [ "$response" == "y" ]; then
        pip install "firebase-admin==2.18.0"
        echo "Please provide the absolute path of where your Google Service Account JSON file is, which contains the keys for your FCM project."
        read response
        if [ ! -z "$response" ]; then
            echo "NOTIFICATION_TYPE = 'FIREBASE'" >> $BD/CentralService/cs_config
            echo "FIREBASE_CREDENTIALS = '$response'" >> $BD/CentralService/cs_config
        fi
    elif [ "$response" == "N" ] || [ "$response" == "n" ]; then
        echo "NOTIFICATION_TYPE = 'RabbitMQ'" >> $BD/CentralService/cs_config
    fi
}

function setup_packages {

    echo
    echo "Securing BD Packages"
    echo "--------------------"
    echo "Enter Y to auto-generate credentials for packages (MongoDB,InfluxDB & Redis). Credentials are stored in cs_config file (or) Enter N to input individual package credentials"
    read response

    if [ "$response" == "Y" ] || [ "$response" == "y" ]; then
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

        sleep 2

        ## Add RabbitMQ Admin user
        rabbitmqUsername="user$(openssl rand -hex 16)"
        rabbitmqPassword=$(openssl rand -hex 32)
        rabbitmqUsername_endUser="user$(openssl rand -hex 16)"
        rabbitmqPassword_endUser=$(openssl rand -hex 32)
        echo "RABBITMQ_ADMIN_USERNAME = '$rabbitmqUsername'">> $BD/DataService/ds_config
        echo "RABBITMQ_ADMIN_PWD = '$rabbitmqPassword'">> $BD/DataService/ds_config
        echo "RABBITMQ_ENDUSER_USERNAME = '$rabbitmqUsername_endUser'">> $BD/DataService/ds_config
        echo "RABBITMQ_ENDUSER_PWD = '$rabbitmqPassword_endUser'">> $BD/DataService/ds_config
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
        echo
        echo "Enter InfluxDB Username: "
        read influxUsername
        echo "Enter InfluxDB Password: "
        read -s influxPassword
        echo "INFLUXDB_USERNAME = '$influxUsername'">> $BD/DataService/ds_config
        echo "INFLUXDB_PWD = '$influxPassword'">> $BD/DataService/ds_config
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
        echo "REDIS_PWD = '$redisPassword'">> $BD/CentralService/cs_config
        echo "REDIS_PWD = '$redisPassword'">> $BD/DataService/ds_config
        echo "    REDIS_PWD = '$redisPassword'" >> $BD/CentralReplica/config.py
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

        echo "RABBITMQ_ADMIN_USERNAME = '$rabbitmqUsername'">> $BD/DataService/ds_config
        echo "RABBITMQ_ADMIN_PWD = '$rabbitmqPassword'">> $BD/DataService/ds_config
        echo "RABBITMQ_ENDUSER_USERNAME = '$rabbitmqUsername_endUser'">> $BD/DataService/ds_config
        echo "RABBITMQ_ENDUSER_PWD = '$rabbitmqPassword_endUser'">> $BD/DataService/ds_config

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

deploy_config
install_packages
if [ "$DEPLOY_CS" = true ]; then
    deploy_centralservice
fi

if [ "$DEPLOY_DS" = true ]; then
    deploy_dataservice
fi

service mongod start
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
setup_notifications


# Create Database on InfluxDB
curl -d "q=CREATE DATABASE buildingdepot" -X POST http://localhost:8086/query
setup_packages
/srv/buildingdepot/venv/bin/python2.7 setup_bd.py "install"
#
echo -e "\nInstallation Finished..\n"
supervisorctl restart all
