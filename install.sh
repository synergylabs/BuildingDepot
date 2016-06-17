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
    if [ "$response" == "y" ]; then
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
    echo 'deb http://www.rabbitmq.com/debian/ testing main' | sudo tee /etc/apt/sources.list.d/rabbitmq.list
    curl -sL https://repos.influxdata.com/influxdb.key | sudo apt-key add -
    source /etc/lsb-release
    echo "deb https://repos.influxdata.com/${DISTRIB_ID,,} ${DISTRIB_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
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
    sudo apt-get install influxdb
    sudo service influxdb start
    sudo apt-get install rabbitmq-server
    sudo apt-get install mailutils
    sed -i -e 's/"inet_interfaces = all/"inet_interfaces = loopback-only"/g' /etc/postfix/main.cf
    service postfix restart
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
    if [ "$response" == "Y" ]; then
        sudo apt-get install mailutils
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
                echo "EMAIL= 'LOCAL'" >> $BD/CentralService/cs_config
                break
            else
                echo "Verification failed. Enter R to retry, Y to use GMail"
                read response
                if [ "$response" == "R" ]; then
                    continue
                elif [ "$response" == 'Y' ]; then
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

popd
setup_email

curl -G http://localhost:8086/query --data-urlencode "q=CREATE DATABASE buildingdepot"
echo -e "\nInstallation Finished..\n"
/srv/buildingdepot/venv/bin/python2.7 setup_bd.py
echo -e "Created a super user with following credentials. Please login and change password immediately \n user id : admin@buildingdepot.org \n password: admin"
