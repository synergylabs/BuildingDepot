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
   :json string host: HostName of the device where the Dataservice is to be installed
   :json string port: Port number of the device where the Dataservice is to be installed

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
      * **host** `(string)` --  HostName of the device where the Dataservice is installed
      * **port** `(string)` --  Port number of the device where the Dataservice is installed


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

This request deletes the requested Dataservice from Building Depot.

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
        "error": " Dataservice does not exist"
      }

