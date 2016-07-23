.. CentralService API Documentation


TagType
#######

Tag Type are used to describe the structure and domains of buildings and help in categorising sensors that can be easily allocated in groups to different users. TagType can be defined in the CentralService at http://www.example.com:81/central/tagtype. TagsTypes have a hierarchical structure i.e. a tag can have both parent tags and children tags. They play a very crucial role within BuildingDepot in defining permissions that restrict access to sensors based on the permissions a user has. Also, A building template is supported by a group of tag types allocated to it.

Add TagType
***********

This request creates a new TagType in BuildingDepot which will be used in the Building template to define the structure of the Buildings.

.. http:post:: /api/tagtype

   :JSON Parameters:
      * **data** `(list)` -- Contains the information of the tag type to be created.
          * **name** `(string)` -- Name of the Tag Type
          * **description** `(string)` `(optional)` -- Description of the Tag Type
          * **Parents** `(string)` `(optional)` --
   :returns:
      * **success** `(array)` -- Returns 'True' if data is posted succesfully otherwise 'False'
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
*********

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