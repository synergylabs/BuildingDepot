.. CentralService API Documentation


DataService
###########

The DataService is where all the data related to sensors and the timeseries data of each sensor resides. All the access control related functionality is defined at centralservice is also enforced within the DataService.  A new DataService can be defined in the CentralService at http://www.example.com:81/central/dataservice.

Create a new DataService
************************

This request creates a new DataService with description,host and port where the datservice will function.

.. http:post:: /api/dataservice

   :json string name: Name of the DataService
   :json string description: Description for the DataService
   :json string host: HostName of the device where the DataService is to be installed
   :json string port: Port number of the device where the DataService is to be installed

   :returns:
      * **success** `(string)` -- Returns 'True' if data is posted successfully otherwise 'False'
      * **error** `(string)` -- An additional value that will be present only if the request fails specifying the cause for failure
   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/dataservice

      {
        "data":{
            "name": "ds3"
            "description":"Test_ds3",
            "host":"127.0.0.3",
            "port":"83"
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
        "error": " Missing parameters"
      }

      {
        "success": "False",
        "error": " Missing data"
      }

Get DataService Details
***********************
This request retrieves name, description, hostname and port to used in the dataservice specified in the request.

.. http:get:: /api/dataservice/<name>

   :param string name: Name of the DataService

   :returns:
      * **success** `(string)` -- Returns 'True' if data is retrieved successfully otherwise 'False'
      * **name** `(string)` -- Name of the DataService
      * **description** `(string)` -- Description for the DataService
      * **host** `(string)` --  HostName of the device where the DataService is installed
      * **port** `(string)` --  Port number of the device where the DataService is installed


   :status 200: Success
   :status 401: Unauthorized Credentials


.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/dataservice/ds3

      Accept: application/json; charset=utf-8

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {   "success": "True",
            "name": "ds3"
            "description":"Test_ds3",
            "host":"127.0.0.3",
            "port":"83"
      }

    **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "False",
        "error": " DataService does not exist"
      }

Delete DataService
******************

This request deletes the requested DataService from Building Depot.

.. http:delete:: /api/dataservice/<name>


   :param string name: Name of the DataService

   :returns:
      * **success** `(string)` -- Returns 'True' if the DataService is successfully deleted otherwise 'False'

   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      DELETE /api/dataservice/ds3
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
        "error": "DataService doesn't exist"
      }

      {
        "success": "False",
        "error": "Cannot delete DataService, contains buildings."
      }

Assign Buildings to DataService
*******************************

This request assigns a specific building to DataService. Once the building is assigned to a specific DataService, the DataService handles sensor datastreams from the building.

.. http:post:: /api/dataservice/<name>/building

   :param string name: Name of the DataService

   :JSON Parameters:
      * **data** `(dict)` -- Contains the information of the buildings to be added to DataService.
          * **buildings** `(list)` -- List of buildings to be added to DataService

   :returns:
      * **success** `(string)` -- Returns 'True' if the building is successfully added to the DataService otherwise 'False'

   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/dataservice/ds1/buildings

      {
        "data":{
          "buildings": ["NSH"]
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
        "error": " Missing parameters"
      }

      {
        "success": "False",
        "error": " Missing data"
      }

      {
        "success": "False",
        "error": "DataService doesn't exist"
      }

      {
        "success": "False",
        "error": "One of the buildings doesn't exist"
      }


Get Building Details from DataService
*************************************

This request retrieves the names of buildings that the specified DataService hosts.

.. http:get:: /api/dataservice/<name>/buildings

   :param string name: Name of the DataService

   :returns:
      * **success** `(string)` -- Returns 'True' if data is retrieved successfully otherwise 'False'
      * **buildings** `(list)` -- Contains the list of buildings that the the specified DataService hosts

   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/dataservice/ds1/buildings

      Accept: application/json; charset=utf-8

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "True",
        "buildings": ["NSH", "GHC"]
      }

   **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "False",
        "error": " DataService doesn't exist"
      }

Remove Buildings from DataService
*********************************

This request removes specified buildings from a DataService.

.. http:delete:: /api/dataservice/<name>/buildings

   :param string name: Name of the DataService

   :JSON Parameters:
      * **data** `(dict)` -- Contains the information of the buildings to be deleted from DataService.
          * **buildings** `(list)` -- List of buildings to be deleted from DataService

   :returns:
      * **success** `(string)` -- Returns 'True' if the buildings are successfully deleted otherwise 'False'

   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      DELETE /api/dataservice/ds1/buildings
      Accept: application/json; charset=utf-8

      {
        "data":{
          "buildings": ["NSH", "GHC"]
        }
      }


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
        "error": "Missing parameters"
      }

      {
        "success": "False",
        "error": "Missing data"
      }

      {
        "success": "False",
        "error": "DataService doesn't exist"
      }

Grant Admin Privileges on DataService
*************************************

This request grants CRUD (create/read/update/delete) privileges on the DataService to the specified users.

.. http:post:: /api/dataservice/<name>/admins

   :param string name: Name of the DataService

   :JSON Parameters:
      * **data** `(dict)` -- Contains the information of the users to whom the CRUD privileges should be given.
          * **admins** `(list)` -- List of the emails(string) of the users.

   :returns:
      * **success** `(string)` -- Returns 'True' if the admin privileges are successfully added to the DataService otherwise 'False'

   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/dataservice/ds1/admins

      {
        "data":{
          "admins": ["user1@buildingdepot.org", "user2@buildingdepot.org"]
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
        "error": " Missing parameters"
      }

      {
        "success": "False",
        "error": " Missing data"
      }

      {
        "success": "False",
        "error": "DataService doesn't exist"
      }

      {
        "success": "False",
        "error": "One of the users doesn\'t exist"
      }


Get List of Admins from DataService
***********************************

This request retrieves the list of users who have the admin privileges on the specified DataService.

.. http:get:: /api/dataservice/<name>/admins

   :param string name: Name of the DataService

   :returns:
      * **success** `(string)` -- Returns 'True' if the list is retrieved successfully otherwise 'False'
      * **admins** `(list)` -- Contains the list of emails of the users who have admin privilege on the specified DataService

   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/dataservice/ds1/buildings

      Accept: application/json; charset=utf-8

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "True",
        "admins": ["user1@buildingdepot.org", "user2@buildingdepot.org"]
      }

   **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "False",
        "error": " DataService doesn't exist"
      }


Revoke Admin Privileges on DataService
**************************************

This request revokes admin privileges on DataService from the specified users.

.. http:delete:: /api/dataservice/<name>/admins

   :param string name: Name of the DataService

   :JSON Parameters:
      * **data** `(dict)` -- Contains the information of the buildings to ba deleted from DataService.
          * **admins** `(list)` -- List of the emails of users whose privileges on DataService should be revoked.

   :returns:
      * **success** `(string)` -- Returns 'True' if the permissions are successfully revoked otherwise 'False'

   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      DELETE /api/dataservice/ds1/admins
      Accept: application/json; charset=utf-8

      {
        "data":{
          "admins": ["user1@buildingdepot.org", "user2@buildingdepot.org"]
        }
      }


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
        "error": "Missing parameters"
      }

      {
        "success": "False",
        "error": "Missing data"
      }

      {
        "success": "False",
        "error": "DataService doesn't exist"
      }
