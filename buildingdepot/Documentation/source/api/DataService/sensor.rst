.. DataService API Documentation


Sensor
######

The Sensor collection manages Sensors for Locations associated with the DataService.
Sensor access is restricted to :ref:`Users <CentralS-Users>` or :ref:`Admins <DataS-Admins>` with
Permissions for the Sensor and to the `Admin` who owns the Sensor.

.. _DataS List Sensors:

List Sensors by Tags or Metadata
********************************
Retreives a list of Sensors accessible to the User initiating the request filtered on the basis of the tags specified by the user

.. http:get:: /api/sensor/list?filter=<filter_type>&param=value

   :param string filter: Type of filter that has to be applied on the sensor list. Valid values are:
                            - "tags"
                            - "metadata"
                         Note: url has to be encoded if it contains characters such as ":"
   :param string param: Name of the filter on the basis of which filtering of the sensors is to be done
   :param string value: Value of the filter on the basis of which filtering of the sensors is to be done
   :returns:
      * **sensors** `(list)` -- List of Sensors (See `View Sensor`_)
   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

   .. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/sensor/list?filter=tags&Floor=3600 HTTP/1.1
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

Create a Sensor
***************

Creates a new Sensor point in BuildingDepot and returns the UUID.

.. http:post:: /api/sensor?name=<Name>&identifier=<Identifier>&building=<building>

   :param string name: Name of the sensor
   :param string identifier: Identifier that user would like to be associated with the Sensor point
   :param string building: Building in which sensor is located

   :returns:
      * **success** `(string)` -- Returns 'True' if data is posted succesfully otherwise 'False'
      * **uuid** `(string)` -- Returns the uuid of the sensor on succesful creation
   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/sensor?id=test_sensor&identifier=Temp_Sensor&building=NSH HTTP/1.1
      Accept: application/json; charset=utf-8

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "True"
        "uuid": "6cf53d24-e3a3-41bd-b2b5-8f109694f628"
      }

Get Sensor details
******************

Retrieves all the details of the sensor based on the uuid specified

.. http:post:: /api/sensor/<name>

   :param string name: Name of the sensor

   :returns:
      * **success** `(string)` -- Returns 'True' if data is retrieved succesfully otherwise 'False'
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

      POST /api/sensor/86ac8207-6372-46a5-ba0b-6b392dbff645
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
          "name": "86ac8207-6372-46a5-ba0b-6b392dbff645",
          "source_identifier": "Sensor Tag",
          "source_name": "SensorTag_1",
          "tags": [
            {
              "name": "Floor",
              "value": "3"
            }
          ]
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

As the names suggest a user with read access to a sensor will be able to read all the datapoints of the sensors. A user with Read/Write access will be able to both read and write (if supported by the sensor) to the sensors. With Deny Read a user will not be able to read any datapoints of the sensor.

The basis of deciding these permissions is dependent on the abstraction of SensorGroups and UserGroups within BuildingDepot.

SensorGroups are created on the basis of tags that are specified at the time of creation. All sensors with the specified tags will be a part of the SensorGroup that is created. Usergroups are basically a list of users which are connected to a SensorGroup via a "Permissions" link. This link is what defines the level of access that the users in the UserGroup have to the sensors in the SensorGroup.

.. raw:: pdf

   OddPageBreak
