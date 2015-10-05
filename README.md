<<<<<<< HEAD
BuildingDepot
=============

BuildingDepot (BD) is a data sensor and actuation system for building management and control. It consists of a central server that uses a RESTful API to send (POST) and retrieve (GET) data. The typical data that BD stores is sensor data for buildings, including data from wireless sensor networks, existing SCADA systems, and other related data sources. 

The BD server consists of three seperate services - the DataService, the DirectoryService, and the UserService.

BD Minimum Requirements
=======================



What's Next
===========

1. Installation
2. Configuration
3. Example Apps/Connectors



Installation
============

To install BD, run the install.sh script in the Installation folder. The default installation location is /opt.
You can provide an installation path to the script e.g. $ ./install.sh /usr. This will cause BD to be installed
at /usr/buildingdepot

By Default, BD uses Https and will attempt to generate an SSL Certificate for the host on which it is installed.

The installer provides a menu of two options:
1. Install/Reinstall BD 
2. Reconfigure an existing BD Installation

Option one will cause any previous installation of BD found at the installation path to be overwritten. It will
also attempt to revert the MySQL and Cassandra databases to a clean install state. Option two allows the admin
to reconfigure an exisiting BD Installation. 


Configuration
=============

BD Configuration consists of the steps outlined below:

1. Provide SuperAdmin Info (Email, Name, Password)
2. Provide BD Host Info (Domain Name, Port)
3. Provide info for SSL Certificate Generation



Example Apps/Connectors
=======================

BD's example apps and connectors can be found in the Tools/Examples folder. They provide a basic skeleton for
developing Apps and Connectors using BD API.

=======
# BuildingDepot-v3
BuildingDepot v3
>>>>>>> 8d06dcdb093edd2ac29bc00907d870581aa7143a
