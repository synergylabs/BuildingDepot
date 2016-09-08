.. DataService API Documentation


Tags
####

Tags can be added to and removed from any sensor using the following requests. Any sensor within a certain building can have tags attached to it that are specifically available for that building only.

Add Tags
********

This request adds the key-value pairs sent, to the tags of the sensor specified by the uuid. The key-value pairs have to be sent along in a list as specified below

Note: The list of tags sent in this request will overwrite the previous list

.. http:post:: /api/sensor/<name>/tags

   :param string sensor_uuid: UUID associated with Sensor
   :JSON Parameters:
      * **data** `(list)` -- Contains the list of tag key-value pairs
          * **name** `(string)` -- Name of the tag point
          * **value** `(string)` -- Value of the tag point
   :returns:
      * **success** `(string)` -- Returns 'True' if data is posted succesfully otherwise 'False'
   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/sensor/26da099a-3fe0-4966-b068-14f51bcedb6e/tags
      Accept: application/json; charset=utf-8


      {
        "data": [
                 {
                  "name": "Corridor",
                  "value": "3600"
                 },
                 {
                  "name": "Room",
                  "value": "3606"
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


Read Tags
**********

This request retrieves two lists of key-value pairs, one list contains the array of eligible tags that can be attached to this sensor and the other list contains the array of tags that are currently attached to this sensor.

.. http:get:: /api/sensor/<name>/tags

   :param string id: UUID associated with Sensor (compulsory)
   :returns:
      * **tags** `(list)` -- Contains the list of tag key-value pairs that are available for the building in which this sensor is located
          * **name** `(string)` -- Name of the tag point
          * **value** `(list)` -- List of eligible values for this certain tag
      * **tags_owned** `(list)` -- Contains the list of tag key-value pairs that are attached to this sensor
          * **name** `(string)` -- Name of the tag point
          * **value** `(string)` -- Value for this tag


   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/sensor/26da099a-3fe0-4966-b068-14f51bcedb6e/tags
      Accept: application/json; charset=utf-8

   **Example response**:

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