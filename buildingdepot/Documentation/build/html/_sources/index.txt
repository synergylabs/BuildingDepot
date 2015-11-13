.. BuildingDepot documentation master file.
   
===================
Building Depot v3.0
===================

Overview
########

This is the official documentaion of BuildingDepot v3.0. BuildingDepot is essentialy an Extensible and Distributed Architecture for Sensor Data Storage, Access and Sharing.


Building Depot has two essential components a Central Service and a Data 
Service :

Central Service - A central directory containing details of all the buildings,users

Data Service - The core component of BD and is responsible for handling the actual sensor data. Exposes a RESTful API for retrieving data and inserting data into the system.

An institution has a single CentralService that houses data of all buildings and user accounts on campus, and multiple DataServices, each of which may contain sensor data of several buildings.

A DataService may belong to any single administrative group that requires sole control over who can access the underlying sensor data points. Different buildings on a campus might desire their own DataService.

Read more about the :ref:`Building Depot<BuildingDepot Overview>`


CentralService
**************

Read more about the :ref:`CentralService<CentralService Overview>`


DataService
***********

Read more about the :ref:`DataService<DataService Overview>`

Download
########

You can get the latest BuildingDepot package (tar.gz) from `www.buildingdepot.org <http://www.buildingdepot.org>`_

`Download version 3.0 <>`_


Install
#######
  
.. toctree::
   :maxdepth: 1
   
   install.rst

REST API Documentation
######################
  
.. toctree::
   :maxdepth: 1
   
   api/CentralService/index.rst
   api/DataService/index.rst
   
.. may be needed for html generation
.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
