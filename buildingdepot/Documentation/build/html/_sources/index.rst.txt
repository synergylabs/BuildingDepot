.. BuildingDepot 3.2.9 documentation master file.

=====================
Building Depot v3.2.9
=====================

Overview
########

This is the official documentation of BuildingDepot v3.2.9. BuildingDepot is essentialy an Extensible and Distributed Architecture for Sensor Data Storage, Access and Sharing.


Building Depot has two essential components a Central Service and a Data Service :

Central Service - A central directory containing details of all the buildings,users

Data Service - The core component of BD and is responsible for handling the actual sensor data. Exposes a RESTful API for retrieving data and inserting data into the system.

An institution has a single CentralService that houses data of all buildings and user accounts on campus, and multiple DataServices, each of which may contain sensor data of several buildings.

A DataService may belong to any single administrative group that requires sole control over who can access the underlying sensor data points. Different buildings on a campus might desire their own DataService.


CentralService
**************

Read more about the CentralService

.. toctree::
   :maxdepth: 2

   centralservice.rst

DataService
***********

Read more about the DataService

.. toctree::
   :maxdepth: 2

   dataservice.rst

Download
########

You can get the latest BuildingDepot package (tar.gz) from `buildingdepot.org <https://iotexpedition.org/software/BuildingDepot-v3.2.7.tar.gz>`_

Install
#######

.. toctree::
   :maxdepth: 1

   install.rst

Getting Started
###############

The `Getting started <https://docs.google.com/a/eng.ucsd.edu/document/d/1XESPZSIt0lIMrCbVb-Uoopa-_t0yNx6uo-d2IBZGLyk/edit?usp=sharing>`_ document will help you guide through the initial setup after installing BuildingDepot.

API Documentation
#################

.. toctree::
   :maxdepth: 1

   api/CentralService/index.rst
   api/DataService/index.rst

.. may be needed for html generation
.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
