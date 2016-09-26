.. CentralService API Documentation


Permission
##########

The Permissions are created between SensorGroups and UserGroups in Building Depot which come together to form the access control lists.Here we select a User Group and a Sensor Group and a permission value with which we want to associate these both. There are three levels of permission defined in BuildingDepot which are ‘d/r’ (deny read) ,’r’ (read), ‘r/w’ (read write) and 'r/w/p' (read write permission). If there are multiple permission mappings between a user and a sensor then the one that is most restrictive is chosen. Permissions can be defined in the CentralService at http://www.example.com:81/central/permission.

Create Permission
*****************

This request creates a new Permission link between a UserGroup and a SensorGroup.

.. http:post:: /api/permission

:JSON Parameters:
  * **data** `(dictionary)` -- Contains the permission value for sensorgroup and usergroup
      * **sensor_group** `(string)` -- Name of the sensor_group
      * **user_group** `(string)` -- Name of the user_group
      * **permission** `(string)` -- Permission level
              * **r** `(string)` -- Read - Will give read only access to the sensors
              * **rw** `(string)` -- Read-Write - Will give read and write access to the sensors
              * **dr** `(string)` -- Deny-read - Will deny any access to the sensors
              * **rwp** `(string)` -- Read-Write-Permission - Highest level of permission that can be assigned. Will give read and write access to the sensors. In addition to this the user will be able to add/remove tags from the sensor.

   :returns:
      * **success** `(string)` -- Returns 'True' if data is posted successfully otherwise 'False'
      * **error** `(string)` -- An additional value that will be present only if the request fails specifying the cause for failure

   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/permission

      {
        "data":{
            "sensor_group":"Test Sensor Group",
            "user_group":"Test User Group",
            "permission":"r"
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
        "error": " User group does not exist"
      }

      {
        "success": "False",
        "error": " Sensor group does not exist"
      }

      {
        "success": "False",
        "error": " Permission value does not exist"
      }

Read Permission
***************

This request retrieves Permission level assigned for existing SensorGroup and UserGroup.

.. http:get:: /api/permission?user_group=<user_group>&sensor_group=<sensor_group>

   :param string user_group: Name of UserGroup (compulsory)
   :param string sensor_group: Name of SensorGroup (compulsory)

   :returns:
      * **success** `(string)` -- Returns 'True' if a permission exists between the sensor and user group otherwise 'False'
      * **permission** `(string)` -- Contains the permission level that are attached to this SensorGroup and UserGroup

   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/permission?user_group=Test User Group&sensor_group=Test Sensor Group
      Accept: application/json; charset=utf-8

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "True"
        "permission": "r"
      }

   **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "False",
        "error": " Permission does not exist"
      }

Delete Permission
*****************

This request deletes the permission link between the UserGroup and SensorGroup

.. http:delete:: /api/permission?user_group=<user_group>&sensor_group=<sensor_group>

   :param string user_group: Name of UserGroup (compulsory)
   :param string sensor_group: Name of SensorGroup (compulsory)

   :returns:
      * **success** `(string)` -- Returns 'True' if a permission is deleted between the sensor and user group otherwise 'False'

   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      DELETE /api/permission?user_group=Test User Group&sensor_group=Test Sensor Group
      Accept: application/json; charset=utf-8

   **Example response**:

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
        "error": " Permission does not exist"
      }

      {
        "success": "False",
        "error": " You are not authorized to delete this permission"
      }

      {
        "success": "False",
        "error": "Missing parameters"
      }