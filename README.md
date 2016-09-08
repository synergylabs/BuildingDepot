BuildingDepot v3.2.5
====================

BuildingDepot (BD) is a data sensor and actuation system for building management and control. It consists of a central server that uses a RESTful API to send (POST) and retrieve (GET) data. The typical data that BD stores is sensor data for buildings, including data from wireless sensor networks, existing SCADA systems, and other related data sources. 

The BD server consists of three seperate services - the DataService, the DirectoryService, and the UserService.

What's Next
===========

1. Installation
2. What's Installed
3. Configuration

Installation
============

To install BD, run the install.sh script in the Installation folder. The default installation location is /srv.

1. Extract the package and cd into the folder**:

$ tar -xzf buildingdepot-3.#.#.tar.gz

$ cd buildingdepot-3.#.#/

2. Run the installer (if running installer using sudo, please consider adding -H flag)

$ ./install.sh

This will install BuildingDepot in the default installation location /srv/buildingdepot with the following directory structure:

buildingdepot
|-- CentralService - CentralService
|-- DataService - DataService
|-- CentralReplica - The central replica that is present at every DataService
+-- venv - Python Virtual Environment

* Note:
This installer installs the BD DataService, CentralService, MongoDB, InfluxDB and Redis on the same machine.The installer also requires requires Mail Transfer Agent or use Gmail APIs. The installer has an optional requirement to use SSL certificates.

What's installed
===============

* The following packages are installed using apt-get
 * openssl
 * python-setuptools
 * python-dev
 * build-essential
 * python-software-properties
 * mongodb
 * python-pip
 * nginx
 * supervisor
 * redis-server
 * influxdb

* The following packages are installed in the python virtual environment
 * Flask
 * mongoengine
 * flask-restful
 * Flask-HTTPAuth
 * flask-login
 * validate-email
 * requests
 * Flask-Script
 * Flask-WTF
 * flask-bootstrap
 * redis
 * influxdb
 * pymongo

Configuration
=============

The BD Installer configures BD with some default values.

The CentralService can be accessed on port 81 and the DataService on port 82.

CentralService

To access the CentralService, go to

   URL - http://<host>:81

DataService

To access the DataService, go to

   URL - http://<host>:82
