.. DataService API Documentation

Apps
####

DataService Apps API allows users interact with the underlying app models. This
API handles the registration and deletion of apps from the system.


Get List of Registered Apps
***************************

This retrieves a list of applications of the current user. This API first
registers the application to the system, then it opens up a rabbitMQ queue.

.. http:get:: /api/apps

   :returns:
      * **success** `(string)` -- Returns 'True' if the list of application is successfully retrieved otherwise 'False'
      * **app_list** `(list(string))` -- The list of the current user's application names.
   :status 200: Success
   :status 401: Unauthorized Credentials  

.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/apps HTTP/1.1
      Accept: application/json; charset=utf-8

   **Example response** (for success):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=utf-8

      {
        "success": "True",
        "app_list": [
          "app_example_1", "app_example_2", "app_example_3"
        ]
      }

   **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application.json; charset=utf-8

      {
        "success": "False",
        "error": "Missing Parameters"
      }

Register a New App
******************

This stores a new app for the current user.

If there already exists an application with the given name, this API call has no effect on BuildingDepot.

.. http:post:: /api/apps

   :JSON Parameters:
      * **data** `(dict)` -- Contains the information of the new application to be registered.
         * **name** `(string)` -- The name of the new application to be registered.

   :returns:
      * **success** `(string)` -- Returns 'True' if adding a new application was successful or an application with the given name already exists. Otherwise 'False'
      * **app_id** `(string)` -- If successful, contains the new RabbitMQ channel ID that corresponds to the new application.

   :status 200: Success
   :status 401: Unauthorized Credentials  

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/apps HTTP/1.1
      Accept: application/json; charset=utf-8

      {
        "data": {
          "name": "new_app_name"
        }
      }

   **Example response** (for success):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
         "success": "True",
         "app_id": ""
      }

   **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "False",
        "error": "Missing Parameters"
      }

      {
        "success": "False",
        "error": "Failed to connect broker"
      }

      {
        "success": "False",
        "error": "Failed to create queue"
      }

Delete an App
*************

This deletes an app of the current user.

.. http:delete:: /api/apps

   :JSON Parameters:
      * **data** `(dict)` -- Contains the information of the application to be deleted.
         * **name** `(string)` -- The name of the application to be deleted.

   :returns:
      * **success** `(string)` -- Returns 'True' if adding a new application was successful or an application with the given name already exists. Otherwise 'False'
      * **error** `(string)` -- Details of an error if unsuccessful

   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      DELETE /api/apps HTTP/1.1
      Accept: application/json; charset=utf-8

      {
        "data": {
          "name": "example_app_name"
        }
      }

   **Example response** (for success):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
         "success": "True",
      }

   **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "False",
        "error": "Missing Parameters"
      }

      {
        "success": "False",
        "error": "Failed to connect broker"
      }

      {
        "success": "False",
        "error": "Failed to delete queue"
      }

Subscribe to a Sensor
*********************

This is used to subscribes to the sensor data.

.. http:post:: /api/apps/subscription

   :JSON Parameters:
      * **data** `(dict)` -- Contains the information about the subscription.
         * **app** `(string)` -- The name of the application.
         * **sensor** `(string)` -- The name of the sensor to subscribe to.

   :returns:
      * **success** `(string)` -- Returns 'True' if subscription was successful. Otherwise 'False'

   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/apps HTTP/1.1
      Accept: application/json; charset=utf-8

      {
        "data": {
          "app": "app_name"
          "sensor": "sensor_uuid"
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
        "error": "Missing Parameters"
      }

      {
        "success": "False",
        "error": "Failed to connect to broker"
      }

      {
        "success": "False",
        "error": "Failed to bind queue"
      }

      {
        "success": "False",
        "error": "App id doesn't exist"
      }

Unsubscribe from a Sensor
*************************

This is used to unsubscribes from the sensor data.

.. http:delete:: /api/apps/subscription

   :JSON Parameters:
      * **data** `(dict)` -- Contains the information about the unsubscription.
         * **app** `(string)` -- The name of the application.
         * **sensor** `(string)` -- The name of the sensor to unsubscribe from.

   :returns:
      * **success** `(string)` -- Returns 'True' if unsubscription was successful. Otherwise 'False'

   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      DELETE /api/apps HTTP/1.1
      Accept: application/json; charset=utf-8

      {
        "data": {
          "app": "app_name"
          "sensor": "sensor_uuid"
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
        "error": "Missing Parameters"
      }

      {
        "success": "False",
        "error": "Failed to connect to broker"
      }

      {
        "success": "False",
        "error": "Failed to bind queue"
      }

      {
        "success": "False",
        "error": "App id doesn't exist"
      }

