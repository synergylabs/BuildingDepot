.. CentralService API Documentation


Metadata
########

Every Sensor within BuildingDepot can have metadata which is essentially a collection of key-value pairs that can be attached to it. This metadata can be used for various purposes one example being searching for sensors within the system based on specific metadata key-value pairs.

Add Metadata
************

This request adds the key-value pairs sent, to the metadata of the sensor specified by the uuid. The key-value pairs have to be sent along in a list as specified below

Note: The list of metadata points sent in this request will overwrite the previously present list

.. http:post:: /api/sensor/<name>/metadata

   :param string sensor_uuid: UUID associated with Sensor
   :JSON Parameters:
      * **data** `(list)` -- Contains the list of metadata key-value pairs
          * **name** `(string)` -- Name of the metadata point
          * **value** `(string)` -- Value of the metadata point
   :returns:
      * **success** `(string)` -- Returns 'True' if data is posted succesfully otherwise 'False'
   :status 200: Success
   :status 401: Unauthorized Credentials  

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/sensor/26da099a-3fe0-4966-b068-14f51bcedb6e/metadata HTTP/1.1
      Accept: application/json; charset=utf-8

      {
        "data":[
                {
                  "name": "MAC",
                  "value": "01:02:03:04:05:06"
                },
                {
                  "name": "Type",
                  "value": "Temperature"
                }
               ]
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "True"
      }


Read Metadata
*************

This retreives a list of the metadata key-value pairs that are attached to the sensor specified in the request.

.. http:get:: /api/sensor/<name>/metadata

   :param string id: UUID associated with Sensor (compulsory)
   :returns:
      * **data** `(list)` -- Contains the list of metadata key-value pairs
          * **name** `(string)` -- Name of the metadata point
          * **value** `(string)` -- Value of the metadata point
   :status 200: Success
   :status 401: Unauthorized Credentials  

.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/sensor/26da099a-3fe0-4966-b068-14f51bcedb6e/metadata HTTP/1.1
      Accept: application/json; charset=utf-8

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "data": [
                 {
                    "name": "MAC",
                    "value": "01:02:03:04:05:06"
                 },
                 {
                    "name": "Type",
                    "value": "Temperature"
                 }
                ]
      }
