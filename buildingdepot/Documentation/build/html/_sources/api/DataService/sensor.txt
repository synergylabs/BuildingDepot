.. DataService API Documentation


Sensor
######

The Sensor collection manages Sensors for Locations associated with the DataService.
Sensor access is restricted to :ref:`Users <CentralS-Users>` or :ref:`Admins <DataS-Admins>` with 
Permissions for the Sensor and to the `Admin` who owns the Sensor.

.. _DataS List Sensors:

List Sensors
************

Retreive a list of Sensors accessible to the User initiating the request. This list
can be context filtered by specifying the context query string.

.. http:get:: /service/api/v1/list

   :returns:
      * **sensors** `(list)` -- List of Sensors (See `View Sensor`_)
   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /service/api/v1/list HTTP/1.1
      Accept: application/json; charset=utf-8

   **Example response**:

   .. sourcecode:: http
   
      HTTP/1.1 200 OK
      Content-Type: application/json
      
      {
        "data": {
          "sensor_1": {
            "building": "NSH", 
            "metadata": {
                 "Type": "Temperature"
            },
            "name": "26da099a-3fe0-4966-b068-14f51bcedb6e", 
            "source_identifier": "SensorTag", 
            "source_name": "Sensor Tag 1", 
            "tags": [
               {
                 "name": "Floor", 
                 "value": "3"
               }
            ]
          }, 
          "sensor_2": {
            "building": "NSH", 
            "metadata": {}, 
            "name": "3a99ca8f-b8c1-4489-b448-d463f0852208", 
            "source_identifier": "SensorTag", 
            "source_name": "Sensor Tag 1", 
            "tags": [
               {
                 "name": "Floor", 
                 "value": "3"
               },
               {
                 "name": "Room",
                 "value": "3600"
               }
          }
        }
      }
      
List Sensors by tag
*******************
Retreives a list of Sensors accessible to the User initiating the request filtered on the basis of the tags specified by the user

.. http:get:: /service/api/v1/<param_1>=<value_1>/tag

   :param string param_1: Name of the tag on the basis of which filtering of the sensors is to be done
   :param string value_1: Value of the tag on the basis of which filtering of the sensors is to be done
   :returns:
      * **sensors** `(list)` -- List of Sensors (See `View Sensor`_)
   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

   .. compound::

   **Example request**:

   .. sourcecode:: http

      GET /service/api/v1/Floor=1/tag HTTP/1.1
      Accept: application/json; charset=utf-8

   **Example response**:

   .. sourcecode:: http
   
      HTTP/1.1 200 OK
      Content-Type: application/json
      
      {
        "data": {
          "sensor_1": {
            "building": "NSH", 
            "metadata": {
                 "Type": "Temperature"
            },
            "name": "26da099a-3fe0-4966-b068-14f51bcedb6e", 
            "source_identifier": "SensorTag", 
            "source_name": "Sensor Tag 1", 
            "tags": [
               {
                 "name": "Floor", 
                 "value": "1"
               }
            ]
          }, 
          "sensor_2": {
            "building": "NSH", 
            "metadata": {}, 
            "name": "3a99ca8f-b8c1-4489-b448-d463f0852208", 
            "source_identifier": "SensorTag", 
            "source_name": "Sensor Tag 1", 
            "tags": [
               {
                 "name": "Floor", 
                 "value": "1"
               },
               {
                 "name": "Room",
                 "value": "3600"
               }
          }
        }
      }

List Sensors by Metadata
************************
Retreives a list of Sensors accessible to the User initiating the request filtered on the basis of the metadata specified by the user

.. http:get:: /service/api/v1/<param_1>=<value_1>/metadata

   :param string param_1: Name of the metadata on the basis of which filtering of the sensors is to be done
   :param string value_1: Value of the metadata on the basis of which filtering of the sensors is to be done
   :returns:
      * **sensors** `(list)` -- List of Sensors (See `View Sensor`_)
   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

   .. compound::

   **Example request**:

   .. sourcecode:: http

      GET /service/api/v1/Type=Temperature/metadata HTTP/1.1
      Accept: application/json; charset=utf-8

   **Example response**:

   .. sourcecode:: http
   
      HTTP/1.1 200 OK
      Content-Type: application/json
      
      {
        "data": {
          "sensor_1": {
            "building": "Wean Hall", 
            "metadata": {
              "Type": "Temperature"
            }, 
            "name": "f8ab0fed-8230-4509-9ae8-42b95a0bf03c", 
            "source_identifier": "SensorTag", 
            "source_name": "SensorTag_1", 
            "tags": [
              {
                "name": "Floor", 
                "value": "3"
              }
            ]
          }
        }
      }

Create a Sensor
***************

Creates a Sensor. 

.. attention::

   Restricted to Admins only

   Currently can only be done through the GUI


Delete a Sensor
***************

Delete the Sensor associated with `sensor_uuid`.

.. attention::

   Restricted to Admins only

   Currently can only be done through the GUI

SensorGroups and UserGroups
***************************

BuildingDepot restricts access to sensors to users on three levels. A user can have either of these types of access to a sensor:
   * **Read**
   * **Read/Write**
   * **Deny Read**

As the names suggest a user with read access to a sensor will be able to read all the datapoints of the sensors. A user with Read/Write access will be able to both read and write (if supported by the sensor) to the sensors. With Deny Read a user will not be able to read any datapoints of the sensor.

The basis of deciding these permissions is dependent on the abstraction of SensorGroups and UserGroups within BuildingDepot.

SensorGroups are created on the basis of tags that are specified at the time of creation. All sensors with the specified tags will be a part of the SensorGroup that is created. Usergroups are basically a list of users which are connected to a SensorGroup via a "Permissions" link. This link is what defines the level of access that the users in the UserGroup have to the sensors in the SensorGroup. 

.. raw:: pdf

   OddPageBreak
