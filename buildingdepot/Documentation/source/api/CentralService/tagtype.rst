.. CentralService API Documentation


TagType
#######

Tag Types are used to describe the structure and domains of buildings and help in categorising sensors that can be easily allocated in groups to different users. TagType can be defined in the CentralService at http://www.example.com:81/api/tagtype. TagsTypes have a hierarchical structure i.e. a tag can have both parent tags and children tags. They play a very crucial role within BuildingDepot in defining permissions that restrict access to sensors based on the permissions a user has. Also, A building template is supported by a group of tag types allocated to it.

Add TagType
***********

This request creates a new TagType in BuildingDepot which will be used in the Building template to define the structure of the Buildings.

.. http:post:: /api/tagtype

   :JSON Parameters:
      * **data** `(list)` -- Contains the information of the tag type to be created.
          * **name** `(string)` -- Name of the Tag Type
          * **description** `(string)` `(optional)` -- Description of the Tag Type
          * **parents** `(string)` `(optional)` -- Parent Tag Types
   :returns:
      * **success** `(array)` -- Returns 'True' if data is posted successfully otherwise 'False'
   :status 200: Success
   :status 401: Unauthorized Credentials  

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/tagtype HTTP/1.1
      Accept: application/json; charset=utf-8


      { "data":
                {   "name": "corridor",
                    "description": "passage in a building",
                    "parents": [ "floor" ]
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
        "error": "List of parents tags not valid"
      }

Get TagType
***********

This request fetches information about a TagType in BuildingDepot.

.. http:get:: /api/tagtype/<name>

   :param string name: Name of the TagType.

   :returns:
      * **success** `(string)` -- Returns 'True' if data is retrieved successfully otherwise 'False'
      * **name** `(string)` -- Name of the Tag Type
      * **description** `(string)` -- Description of the Tag Type
      * **parents** `(string)` -- Parents of this Tag Type.
      * **children** `(string)` -- Children of this Tag Type.
   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/tagtype/floor HTTP/1.1
      Accept: application/json; charset=utf-8

   **Example response** (for success):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "True"
        "children": [  "corridor"
                        ],
        "description": null,
        "name": "floor",
        "parents": [],
        "success": "True"

      }

   **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "False",
        "error": "TagType does not exist"
      }