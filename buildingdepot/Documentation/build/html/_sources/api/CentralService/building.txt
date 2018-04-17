.. CentralService API Documentation


Buildings
#########

All the buildings that are present within the deployment of BuildingDepot are defined here. When adding a new building a BuildingTemplate has to be selected which defines the structure of this building. The tags that are available to be assigned to this building are dependent on the BuildingTemplate. Tags can be selected and the values for each of them can be specified here. Each tag can have multiple values specified for it. Building can be defined in the CentralService at http://www.example.com:81/central/building.

Create a new Building
*********************

This request creates a new Building with name, description and building template to be used in the building specified by the user.

.. http:post:: /api/building

   :json string name: Name of the Building
   :json string description: Description for the Building
   :json string template: Name of a BuildingTemplate

   :returns:
      * **success** `(string)` -- Returns 'True' if data is posted successfully otherwise 'False'
      * **error** `(string)` -- An additional value that will be present only if the request fails specifying the cause for failure
   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/building

      {
        "data":{
            "name":"Test_Building",
            "description":"New Building",
            "template":"Test_Building_Template"
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
        "error": " BuildingTemplate does not exist"
      }

      {
        "success": "False",
        "error": " Missing parameters"
      }

      {
        "success": "False",
        "error": " Missing data"
      }

Get Building Details
********************
This request retrieves name, description and template to used in the building specified in the request.

.. http:get:: /api/building/<name>

   :param string name: Name of the Building

   :returns:
      * **success** `(string)` -- Returns 'True' if data is retrieved successfully otherwise 'False'
      * **name** `(string)` -- Name of the Building
      * **description** `(string)` -- Description for the Building
      * **template** `(string)` --  BuildingTemplate assigned for the Building.

   :status 200: Success
   :status 401: Unauthorized Credentials


.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/building/Test_Building

      Accept: application/json; charset=utf-8

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {   "success": "True",
          "name": "Test_Building",
          "description":"New Building",
          "template": "Test_Building_Template"
      }

    **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "False",
        "error": " Building does not exist"
      }

Delete Building
***************

This request deletes the requested Building and the template assigned to it.

.. http:delete:: /api/building/<name>


   :param string name: Name of the Building

   :returns:
      * **success** `(string)` -- Returns 'True' if the Building is successfully deleted otherwise 'False'

   :status 200: Success
   :status 401: Unauthorized Credentials

.. compound::

   **Example request**:

   .. sourcecode:: http

      DELETE /api/building/Test_Building
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
        "error": " Building does not exist"
      }

      {
        "success": "False",
        "error": " Building is in use"
      }
