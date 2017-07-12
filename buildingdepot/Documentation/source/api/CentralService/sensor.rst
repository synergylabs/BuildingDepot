.. CentralService API Documentation


Sensor
######

The Sensor collection manages Sensors for Locations associated with the CentralService.Sensors can be defined in the CentralService at http://www.example.com:81/central/sensor.
Sensor access is restricted to :ref:`Users <CentralS-Users>` or :ref:`Admins <DataS-Admins>` with
Permissions for the Sensor and to the `Admin` who owns the Sensor.

Create a Sensor
***************

Creates a new Sensor point in BuildingDepot and returns the UUID.

.. http:post:: /api/sensor

   :json string name: Name of the sensor
   :json string identifier: An identifier that will be associated with the sensor
   :json string building: Building in which the sensor is located
   :json string sensortype (optional): Type of Sensor (occupancy_sensor) 

   :returns:
      * **success** `(string)` -- Returns 'True' if data is posted succesfully otherwise 'False'
      * **uuid** `(string)` -- Returns sensortype:name of the sensor on succesful creation. Stands as UUID of sensor. If sensortype not provided sensortype = "BasicBD"
   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/sensor HTTP/1.1
      Accept: application/json; charset=utf-8

      {
        "name":"Test Sensor",
        "identifier":"Sensor Tag",
        "building":"NSH"
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "True"
        "uuid": "BasicBD:Test Sensor"
      }

Get Sensor details
******************

Retrieves all the details of the sensor based on the sensor name specified

.. http:get:: /api/sensor/<name>

   :param string name: Name of the sensor

   :returns:
      * **success** `(string)` -- Returns 'True' if data is retrieved successfully otherwise 'False'
      * **building** `(string)` -- Building in which the sensor is located
      * **name** `(string)` -- Name of the sensor
      * **tags** '(list)' -- List of tags owned by the sensor
      * **metadata** '(list)' -- List of metadata owned by the sensor
      * **source_identifier** '(dictionary)' -- Source identifier of the sensor
      * **source_name** '(dictionary)' -- Source name of the sensor
   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/sensor/BasicBD:Test Sensor
      Accept: application/json; charset=utf-8

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
          "building": "NSH",
          "metadata": [
            {
              "name": "MAC",
              "value": "01:02:03:04:05:06"
            },
            {
              "name": "Type",
              "value": "Temperature"
            }
          ],
          "name": "BasicBD:Test Sensor",
          "source_identifier": "Sensor Tag",
          "source_name": "SensorTag_1",
          "tags": [
            {
              "name": "Floor",
              "value": "3"
            }
          ]
    }

Search Sensors
**************

The Search API is used search sensors based on sensor_name,source_name,source_identifier, building, Tag. Multiple search queries can be sent in a single request. Optional additional functionality: Recusrive search on type or Tags. Adding * to the tag-type (e.g. isLocatedIn*:Floor:1) will resurively search for anything that Floor:1 isLocatedIn. For use in graphical ontologies which use tags as edges (see Brick ontology). If SensorA islocatedIn Floor:1 and Floor:1 islocatedIn Building:NSH, then SensorA islocatedIn* BuildingNSH. 
.. http:post:: /api/search

:JSON Parameters:
  * **data** `(dictionary)` -- Contains the list of Search Query key-value pairs
      * **ID** `(string)` -- Name of the Sensor
      * **Building** `(string)` -- Building in which the sensor is located
      * **Tags** '(dictionary)' -- List of tags owned by the sensor. The are given as key,value pairs.
      * **Source_Identifier** '(dictionary)' -- Source identifier of the sensor
      * **Source_Name** '(dictionary)' -- Source name of the sensor
      * **Type** `(string)` -- Type of Sensor in Ontology (e.g. Occupancy_Sensor, BasicBD, Temperature_Sensor)
.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/search

      {
        "data":{
            "ID":"Occupancy_Sensor:OCRM104",
            "Building":"NSH"
            "Tags":["floor:1"]
        }
      }

   **Example response** (for success):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
          "success": "True",
          "building": "NSH",
          "metadata": [],
          "name": "Occupancy_Sensor:OCRM104",
          "source_identifier": "Sensor Tag",
          "source_name": "Test Sensor",
          "tags": [
              "name": "Floor",
              "value": "1"
          ]
      }

   **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "False",
        "error": " Sensor does not exist"
      }

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
   * **Read/Write/Permission**

As the names suggest a user with read access to a sensor will be able to read all the datapoints of the sensors. A user with Read/Write access will be able to both read and write (if supported by the sensor) to the sensors. With Deny Read a user will not be able to read any datapoints of the sensor.

The basis of deciding these permissions is dependent on the abstraction of SensorGroups and UserGroups within BuildingDepot.

SensorGroups are created on the basis of tags that are specified at the time of creation. All sensors with the specified tags will be a part of the SensorGroup that is created. Usergroups are basically a list of users which are connected to a SensorGroup via a "Permissions" link. This link is what defines the level of access that the users in the UserGroup have to the sensors in the SensorGroup.

.. raw:: pdf

   OddPageBreak
