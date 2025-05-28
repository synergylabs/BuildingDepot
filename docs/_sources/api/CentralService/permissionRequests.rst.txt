.. CentralService API Documentation


Permission Requests
###################

A Permission Request can be sent to obtain access to a particular sensor entity owned by a user of BuildingDepot.
Once the permission request is sent to the user, on approval the Permission APIs should be used to create a permission
pair between the user and the sensor resources.
The Permissions are created between SensorGroups and UserGroups in Building Depot which come together to form the access control lists.
Here we select a User Group and a Sensor Group and a permission value with which we want to associate these both.
There are three levels of permission defined in BuildingDepot which are ‘d/r’ (deny read) ,’r’ (read), ‘r/w’ (read write) and 'r/w/p' (read write permission).
If there are multiple permission mappings between a user and a sensor then the one that is most restrictive is chosen.
Permissions can be defined in the CentralService at http://www.example.com:81/api/permission.
Note: Firebase or RabbitMQ needs to be installed during the BD installation for this to work.

Create Permission Requests
**************************

This request creates a new Permission Request for a sensor entity owned by a user.

.. http:post:: /api/permission/request

:JSON Parameters:
  * **data** `(dictionary)` -- Contains the permission value for sensorgroup and usergroup
      * **target_sensors** `(string)` -- List of Targeted sensors
      * **timestamp** `(string)` -- Name of the user_group
      * **permission** `(string)` -- Permission level
              * **r** `(string)` -- Read - Will give read only access to the sensors
              * **rw** `(string)` -- Read-Write - Will give read and write access to the sensors
              * **dr** `(string)` -- Deny-read - Will deny any access to the sensors
              * **rwp** `(string)` -- Read-Write-Permission - Highest level of permission that can be assigned. Will give read and write access to the sensors. In addition to this the user will be able to add/remove tags from the sensor.

   :returns:
      * **success** `(string)` -- Returns 'True' if data is posted successfully otherwise 'False'
      * **error** `(string)` -- An additional value that will be present only if the request fails specifying the cause for failure

   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/permission/request HTTP/1.1
      Accept: application/json; charset=utf-8

      {
        "data":{
            "target_sensors":[6cf53d24-e3a3-41bd-b2b5-8f109694f628, 6cf53d24-e3a3-41bd-b2b5-8f109694f629],
            "timestamp":"1626105964",
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
        "error": " Missing Parameters"
      }

      {
        "success": "False",
        "error": " Sensor does not exist"
      }

      {
        "success": "False",
        "error": " Permission value does not exist"
      }

Read Permission Requests
************************

This request retrieves Permission Request for a user.

.. http:get:: /api/permission/request

   :returns:
      * **success** `(string)` -- Returns 'True' if a permission exists between the sensor and user group otherwise 'False'
      * **permission_requests** `(string)` -- Contains the permission level that are attached to this SensorGroup and UserGroup

   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/permission/request HTTP/1.1
      Accept: application/json; charset=utf-8

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "True"
        "permission_requests": [{ "requester_name": Admin, "requester_email": test@buildingdepot.org, "requested_sensors": [6cf53d24-e3a3-41bd-b2b5-8f109694f628, 6cf53d24-e3a3-41bd-b2b5-8f109694f629] }]
      }

   **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "False",
        "error": " Permission Requests does not exist"
      }