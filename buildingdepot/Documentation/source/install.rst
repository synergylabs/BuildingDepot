.. _BuildingDepot Installation:

Installation
############

Get BD
******
Download from http://www.buildingdepot.org/downloads.html

Using install.sh
****************

.. note::

   This installer installs the BD DataService, CentralService, MongoDB, InfluxDB
   and Redis on the same machine.

1. Extract the package and cd into the folder**:
   
   :code:`$ tar -xzf buildingdepot-3.#.#.tar.gz`
   
   :code:`$ cd buildingdepot-3.#.#/`

#. Run the installer

   :code:`$ ./install.sh`

   This will install BuildingDepot in the default installation location 
   :code:`/srv/buildingdepot` with the following directory structure:

   .. code:: bash
   
      buildingdepot
      |-- CentralService - CentralService
      |-- DataService - DataService
      |-- CentralReplica - The central replica that is present at every DataService
      +-- venv - Python Virtual Environment

What's installed
****************
   
-  The following packages are installed using apt-get

   .. code:: bash

      openssl
      python-setuptools 
      python-dev 
      build-essential 
      python-software-properties
      mongodb
      python-pip
      nginx
      supervisor
      redis-server
      influxdb
   
-  The following packages are installed in the python virtual environment

   .. code:: bash
   
      Flask
      mongoengine
      flask-restful
      Flask-HTTPAuth
      flask-login
      validate_email
      requests
      Flask-Script
      Flask-WTF
      flask-bootstrap
      redis
      influxdb
      pymongo


.. _Configuration:

Configuration
#############

The BD :ref:`Installer <BuildingDepot Installation>` configures BD with some default values.

The CentralService can be accessed on port 81 and the DataService on port 81.

.. _Access DataService:

DataService
***********

To access the DataService, go to

.. code:: bash

  URL - http://<host>:82

.. _Access CentralService:

CentralService
**************
To access the CentralService, go to

.. code:: bash

   URL - http://<host>:81
