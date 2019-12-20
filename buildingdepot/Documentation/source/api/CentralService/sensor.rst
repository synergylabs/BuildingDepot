.. CentralService API Documentation


Sensor
######

The Sensor collection manages Sensors for Locations associated with the CentralService.Sensors can be defined in the CentralService at http://www.example.com:81/api/sensor.
Sensor access is restricted to Central Service `Users` with permissions for the Sensor and to the `Admin` who owns the Sensor.

Create a Sensor
***************

Creates a new Sensor point in BuildingDepot and returns the UUID.

.. http:post:: /api/sensor

   :json string name: Name of the sensor
   :json string identifier: An identifier that will be associated with the sensor
   :json string building: Building in which the sensor is located

   :returns:
      * **success** `(string)` -- Returns 'True' if data is posted successfully otherwise 'False'
      * **uuid** `(string)` -- Returns the uuid of the sensor on successful creation
   :status 200: Success
   :status 401: Unauthorized Credentials  

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/sensor HTTP/1.1
      Accept: application/json; charset=utf-8

      {
            "data": {
                      "name":"Test_Sensor",
                      "identifier":"Sensor_Tag",
                      "building":"NSH"
                    }
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "True"
        "uuid": "6cf53d24-e3a3-41bd-b2b5-8f109694f628"
      }

Create a Sensor View
********************

Creates a new Sensor View for a sensor point in BuildingDepot. Each sensor may have multiple fields of data, however,
the user may only want to receive or request a subset of data. This API creates a view for the sensor and returns the
UUID for the sensor.

.. http:post:: /api/sensor/<name>/view

   :param string id: UUID associated with Sensor (required)

   :JSON Parameters:
      * **data** `(dictionary)` -- Contains the information of the sensor view.
          * **fields** `(string)` -- The data fields of the sensor that is being posted to BD.
          * **source_name** `(string)` -- Name of the sensor view

   :returns:
      * **success** `(dictionary)` -- Returns 'True' if data is posted successfully otherwise 'False'
   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/sensor/8aac1048-aa9f-41c9-9c20-6dd81339c7de/views HTTP/1.1
      Accept: application/json; charset=utf-8

      {
            "data":{
                    "fields": "EMI-1, Temp-2",
                    "source_name": "Important Values"
                    }
      }

   **Example response** (for success):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "True"
        "uuid": "6cf53d24-e3a3-41bd-b2b5-8f109694f628"
      }

   **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "False",
        "error": "Communication failure with DataService"
      }

Get Sensor details
******************

Retrieves all the details of the sensor based on the uuid specified

.. http:get:: /api/sensor/<name>

   :param string name: uuid of the sensor

   :returns:
      * **success** `(string)` -- Returns 'True' if data is retrieved successfully otherwise 'False'
      * **building** `(string)` -- Building in which the sensor is located
      * **name** `(string)` -- UUID name of the sensor
      * **tags** `(list)` -- List of tags owned by the sensor
      * **metadata** `(list)` -- List of metadata owned by the sensor
      * **source_identifier** `(dictionary)` -- Source identifier of the sensor
      * **source_name** `(dictionary)` -- Source name of the sensor
   :status 200: Success
   :status 401: Unauthorized Credentials  

.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/sensor/8aac1048-aa9f-41c9-9c20-6dd81339c7de/views HTTP/1.1
      Accept: application/json; charset=utf-8

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
          "success": "True",
          "views_owned": [
            {
              "fields": "EMI-0",
              "id": "280bc754-a963-4740-89f4-bdae9ede76f6",
              "source_name": "Averages"
            },
            {
              "fields": "EMI-2, EMI-3",
              "id": "6336a9d7-6f65-4572-9e52-78fa3808c92f",
              "source_name": "Min, Max EMI"
            }
          ]
      }

Get Sensor View details
***********************

Retrieves all the views of the sensor based on the sensor uuid specified

.. http:get:: /api/sensor/<name>/views

   :param string name: uuid of the sensor

   :returns:
      * **success** `(string)` -- Returns 'True' if data is retrieved successfully otherwise 'False'
      * **views_owned** `(list)` -- List of views for the sensor.
        * **fields** `(string)` -- A subset of fields in the sensor
        * **id** `(string)` -- UUID name of the views of the sensor
        * **source_name** `(string)` -- Source name of the views of the sensor

   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/sensor/6cf53d24-e3a3-41bd-b2b5-8f109694f628 HTTP/1.1
      Accept: application/json; charset=utf-8

   **Example response** (for success):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {   "building": "NSH",
          "name": "86ac8207-6372-46a5-ba0b-6b392dbff645",
          "source_identifier": "Sensor_Tag",
          "source_name": "Test_Sensor"
      }

   **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "False",
        "error": " Sensor does not exist"
      }

   **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "False",
        "error": "Missing parameters"
      }

Search Sensors
**************

The Search API is used search sensors based on uuid,source_name,source_identifier, building, Tag and MetaData. Multiple search queries can be sent in a single request.

.. http:post:: /api/sensor/search

:JSON Parameters:
  * **data** `(dictionary)` -- Contains the list of Search Query key-value pairs
      * **ID** `(list)` -- UUID of the Sensor
      * **Building** `(list)` -- Building in which the sensor is located
      * **Tags** `(list)` -- List of tags owned by the sensor. The are given as key,value pairs.
      * **Metadata** `(list)` -- List of metadata owned by the sensor.The are given as key,value pairs.
      * **Source_Identifier** `(list)` -- Source identifier of the sensor
      * **Source_Name** `(list)` -- Source name of the sensor

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/sensor/search HTTP/1.1
      Accept: application/json; charset=utf-8

      {
        "data":{
            "ID":["6cf53d24-e3a3-41bd-b2b5-8f109694f628"],
            "Building":["NSH"],
            "Tags":["floor:1", "corridor:4200"]
        }
      }

   **Example response** (for success):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
          "success": "True",
          "building": "NSH",
          "name": "6cf53d24-e3a3-41bd-b2b5-8f109694f628",
          "source_identifier": "Sensor Tag",
          "source_name": "Test Sensor",
          "tags":[{"name": "floor", "value": "1"}, {"name": "corridor", "value": "4200"}]
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

Delete a Sensor View
********************

This request deletes a sensor view of a sensor.

.. http:delete:: /api/sensor/<uuid>/views/<view_uuid>

   :param string uuid: UUID of the sensor.
   :param string view_uuid: UUID of the view sensor.
   :returns:
      * **success** `(string)` -- Returns 'True' if the UserGroup is successfully deleted otherwise 'False'

   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      DELETE /api/sensor/8aac1048-aa9f-41c9-9c20-6dd81339c7de/views/22d807bf-af67-493a-80b7-2690d26c9244 HTTP/1.1
      Accept: application/json; charset=utf-8

   **Example response** (for success):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "True"
      }

   **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "False",
        "error": "Permission does not exist"
      }

   **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "False",
        "error": "Communication failure with DataService"
      }

Add Tags to a Sensor
*********************

This request adds tags (key-value pairs) to a particular sensor. To get the available tags that can be added to the sensor, please use the get tags of a sensor API to fetch the list of available tags.

.. http:post:: /api/sensor/<name>/tags

   :param string id: UUID associated with Sensor (required)

   :JSON Parameters:
      * **data** `(dictionary)` -- Contains the information of the tag to be added to the sensor.
          * **tags** `(list)` -- List of tags
              * **name** `(string)` -- Name of the Tag Type
              * **value** `(string)` -- Value for the Tag Type
   :returns:
      * **success** `(array)` -- Returns 'True' if data is posted successfully otherwise 'False'
   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/sensor/be2a09a5-4ef6-4c67-886e-272c37e7e38f/tags HTTP/1.1
      Accept: application/json; charset=utf-8

      {
            "data":{
                    "tags": [
                            {
                                "name": "Room",
                                "value": "4120"
                            },
                            {
                                "name": "floor",
                                "value": "1"
                            }
                        ]
                    }
      }

   **Example response** (for success):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "True"
      }

   **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "False",
        "error": " Sensor does not exist"
      }

Get Tags of a Sensor
*********************

This request retrieves two lists of key-value pairs, one list contains the array of eligible tags that can be attached to this sensor and the other list contains the array of tags that are currently attached to this sensor.

.. http:get:: /api/sensor/<name>/tags

   :param string id: UUID associated with Sensor (required)
   :returns:
      * **tags** `(list)` -- Contains the list of tag key-value pairs that are available for the building in which this sensor is located
          * **name** `(string)` -- Name of the tag point
          * **value** `(list)` -- List of eligible values for this certain tag
      * **tags_owned** `(list)` -- Contains the list of tag key-value pairs that are attached to this sensor
          * **name** `(string)` -- Name of the tag point
          * **value** `(string)` -- Value for this tag


   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/sensor/26da099a-3fe0-4966-b068-14f51bcedb6e/tags HTTP/1.1
      Accept: application/json; charset=utf-8

   **Example response** (for success):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "tags": {
                 "Corridor": [
                              "3600",
                              "3700"
                             ],
                 "Floor": [
                           "3"
                          ],
                 "Room": [
                          "3606"
                         ]
                },
        "tags_owned": [
                        {
                         "name": "Corridor",
                         "value": "3600"
                        },
                        {
                         "name": "Floor",
                         "value": "3"
                        },
                        {
                         "name": "Room",
                         "value": "3606"
                        }
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
