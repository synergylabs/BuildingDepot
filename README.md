BuildingDepot v3.3 ([link](https://buildingdepot.org/))
====================

![BuildingDepot](https://github.com/synergylabs/BuildingDepot-v3/workflows/BuildingDepot/badge.svg)

BuildingDepot (BD) is a data sensor and actuation system for building management and control. It consists of a central server that uses a RESTful API to send (POST) and retrieve (GET) data. The typical data that BD stores is sensor data for buildings, including data from wireless sensor networks, existing SCADA systems, and other related data sources. 

The BD server consists of three separate services - the DataService, the DirectoryService, and the UserService.

What's Next
===========

1. Installation
2. What's Installed
3. Configuration

Installation
============

To install BD, you can just run the install.sh script in the installation folder. The default installation location is /srv.

1. Extract the package and cd into the folder**:

    ```shell
    $ tar -xzf buildingdepot-3.#.#.tar.gz 
    $ cd buildingdepot-3.#.#/
    ```
   
2. Run the installer (if running the installer using sudo, please consider adding -H flag)

    ```shell
    $ ./install.sh
    ```
This will install BuildingDepot in the default installation location /srv/buildingdepot with the following directory structure:

- buildingdepot
    - CentralService - CentralService
    - DataService - DataService
    - CentralReplica - The central replica that is present at every DataService
    - venv - Python Virtual Environment

* Note:
This installer installs the BD DataService, CentralService, MongoDB, InfluxDB and Redis on the same machine. The installer also requires a Mail Transfer Agent or Gmail APIs. The installer has an optional requirement to use SSL certificates.

Upgrade to New BD Version
=========================
To upgrade to a new version of BD for an existing installation, 
run the upgrade_to_latest_BD.sh script in the scripts folder. The 
default installation location is /srv.

1. Extract the new package and cd into the folder:

    ```shell
    $ tar -xzf buildingdepot-3.#.#.tar.gz
    $ cd buildingdepot-3.#.#/
    ```
   
2. cd into the scripts folder:
    ```shell
     $ cd scripts/
    ```

3. Run the installer (if running installer using sudo, please consider adding -H flag)
    ```shell
    $ ./install.sh
    ```

Configuration
=============

The BD Installer configures BD with some default values.

The CentralService can be accessed on port 81, and the DataService on port 82.

CentralService

To access the CentralService, go to

   URL - https://<host>:81

DataService

To access the DataService, go to

   URL - https://<host>:82

What's installed
===============

* The following packages are installed using apt-get
 * openssl
 * python3-setuptools
 * python3-dev
 * build-essential
 * python3-software-properties
 * mongodb
 * python3-pip
 * nginx
 * supervisor
 * redis-server
 * influxdb

* The following packages are installed in the python virtual environment
 * Flask
 * mongoengine
 * Flask-Login
 * Flask-Script
 * Flask-OAuthlib
 * jsonschema
 * pika
 * Sphinx
 * sphinx-theme
 * Flask-WTF
 * Flask-Bootstrap
 * uWSGI
 * redis
 * influxdb
 * pymongo
 * aniso8601
 * firebase-admin
