.. CentralService API Documentation


BuildingTemplate
################

Each building within BuildingDepot has a BuildingTemplate as a foundation. The BuildingTemplate helps define the structure of the building. The user has to assign a set of tags to the BuildingTemplate on creation which can be used later on for all the sensors within that building. BuildingTemplate can be defined in the CentralService at http://www.example.com:81/api/buildingtemplate.

Create a Building Template
**************************

This request creates a Building Template with the name, description and tagtypes to be used in the buildingtemplate specified by the user.

.. http:post:: /api/template

   :json string name: Name of the BuildingTemplate
   :json string description: Description for the BuildingTemplate
   :json list tag_types: List of TagTypes available in system

   :returns:
      * **success** `(string)` -- Returns 'True' if data is posted successfully otherwise 'False'
      * **error** `(string)` -- An additional value that will be present only if the request fails specifying the cause for failure
   :status 200: Success
   :status 401: Unauthorized Credentials 

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/template HTTP/1.1
      Accept: application/json; charset=utf-8

      {
        "data":{
            "name":"Test_Building_Template",
            "description":"New Building Template",
            "tag_types":["floor","room","corridor"]
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
        "error": " One of the TagTypes doesn't exist"
      }

      {
        "success": "False",
        "error": " Missing parameters"
      }

      {
        "success": "False",
        "error": " Missing data"
      }

Get BuildingTemplate Details
****************************

This request retrieves name, description and tagtypes used in the buildingtemplate specified in the request.

.. http:get:: /api/template/<name>

   :param string name: Name of the BuildingTemplate

   :returns:
      * **success** `(string)` -- Returns 'True' if data is retrieved successfully otherwise 'False'
      * **name** `(string)` -- Name of the BuildingTemplate
      * **description** `(string)` -- Description for the BuildingTemplate
      * **tag_types** `(list)` --  List of TagTypes assigned for the BuildingTemplate

   :status 200: Success
   :status 401: Unauthorized Credentials  


.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/template/Test_Building_Template HTTP/1.1
      Accept: application/json; charset=utf-8

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {   "success": "True",
          "name": "Test_Building_Template",
          "description":"New Building Template",
          "tags": ["floor","room","corridor"]
      }

   **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {  "success": "False",
        "error": " BuildingTemplate does not exist"
        }


Delete Building Template
************************

This request deletes the requested BuildingTemplate and the Tagtypes assigned to it.

.. http:delete:: /api/template/<name>


   :param string name: Name of the BuildingTemplate

   :returns:
      * **success** `(string)` -- Returns 'True' if the Building Template is successfully deleted otherwise 'False'

   :status 200: Success
   :status 401: Unauthorized Credentials  

.. compound::

   **Example request**:

   .. sourcecode:: http

      DELETE /api/template/Test_Building_Template  HTTP/1.1
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
        "error": " BuildingTemplate does not exist"
      }

      {
        "success": "False",
        "error": " BuildingTemplate is in use"
      }