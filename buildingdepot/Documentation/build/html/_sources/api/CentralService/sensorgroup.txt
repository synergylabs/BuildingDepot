.. CentralService API Documentation


SensorGroups
############

SensorGroups are a virtual collection of sensors that are created based on the tags that are specified. The list of sensors that belong to a SensorGroup can be changed by modifying the tags attached to this SensorGroup. All sensors having the current tags will fall under this SensorGroup automatically for any subsequent operations.SensorGroups can be defined in the CentralService at http://www.example.com:81/central/sensorgroup.

Create SensorGroup
******************

This request creates a new SensorGroup with the name and description in the building specified by the user.

.. http:post:: /api/sensor_group

   :json string name: Name of the sensor group
   :json string building: Building to which this sensor group belongs
   :json string description: Description for the sensor group

   :returns:
      * **success** `(string)` -- Returns 'True' if data is posted succesfully otherwise 'False'
      * **error** `(string)` -- An additional value that will be present only if the request fails specifying the cause for failure
   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/sensor_group

      {
        "name":"Test Sensor Group",
        "building":"NSH",
        "description":"Description for Sensor Group"
      }

   **Example response** (for succcess):

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
        "error": "Building does not exist"
      }

Add tags to SensorGroup
***********************

This request adds the tags specified in the request to the SensorGroup

Note: The list of tags sent in this request will overwrite the previous list.

.. http:post:: /api/sensor_group/<name>/tags

   :param string name: Name of SensorGroup
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

      POST /api/sensor_group/test/tags
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


Get list of tags in SensorGroup
********************************

This request retrieves two lists of key-value pairs, one list contains the array of eligible tags that can be attached to this SensorGroup and the other list contains the array of tags that are currently attached to this SensorGroup.

.. http:get:: /api/sensor_group/<name>/tags

   :param string name: Name of SensorGroup (compulsory)
   :returns:
      * **tags** `(list)` -- Contains the list of tag key-value pairs that are available for the building in which this SensorGroup is located
          * **name** `(string)` -- Name of the tag point
          * **value** `(list)` -- List of eligible values for this certain tag
      * **tags_owned** `(list)` -- Contains the list of tag key-value pairs that are attached to this SensorGroup
          * **name** `(string)` -- Name of the tag point
          * **value** `(string)` -- Value for this tag


   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/sensor_group/test/tags
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