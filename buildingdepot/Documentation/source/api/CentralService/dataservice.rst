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
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

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
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)


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
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

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

This request assigns a specific building to DataService. Once the building is assigned to a specific DataService, the DataService can handles sensor streams in the building.

.. http:post:: /api/dataservice/<name>/building

   :param string name: Name of the DataService

   :returns:
      * **success** `(string)` -- Returns 'True' if the building is successfully added to the DataService otherwise 'False'

   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/dataservice/ds1/buildings

      {
        "data":{
          "building": "NSH"
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
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

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
      * **data** `(dict)` -- Contains the information of the buildings to ba deleted from DataService.
          * **buildings** `(list)` -- List of buildings to be deleted from DataService

   :returns:
      * **success** `(string)` -- Returns 'True' if the buildings are successfully deleted otherwise 'False'

   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

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
