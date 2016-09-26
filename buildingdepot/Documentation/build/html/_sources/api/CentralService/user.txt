.. CentralService API Documentation


User
####

The Users of BuildingDepot have either of the two roles SuperUser and Default User through which we maintain the access control. The Super User is the admin of BuildingDepot who has permission to add,remove,read,write,delete any entity. The Default User has limited access and does not have permission to add,remove any building and dataservice related entity.Only the SuperUser can add another user and the SuperUser by default in every Building Depot installtion is admin@buildingdepot.org. A new User can be added by the SuperUser in the CentralService at http://www.example.com:81/central/user.

Add a new User
**************

This request creates a new  User in the Central Service. Only the SuperUser can add a new user

.. http:post:: /api/user

   :json string first_name: First Name of the User
   :json string last_name: Last Name of the User
   :json string email: email of the User
   :json string role: role of the User
              * **super** `(string)` -- super- Has access to all the entities in Building Depot
              * **default** `(string)` -- default - limited access to entities in Building Depot

   :returns:
      * **success** `(string)` -- Returns 'True' if data is posted successfully otherwise 'False'
      * **error** `(string)` -- An additional value that will be present only if the request fails specifying the cause for failure
   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/user

      {
        "data":{
            "first_name": "New"
            "last_name":"User",
            "email":"newuser@gmail.com",
            "role":"super"
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
        "error": "User already exists"
      }

      {
        "success": "False",
        "error": " Missing parameters"
      }

      {
        "success": "False",
        "error": " Missing data"
      }

Get User Details
****************
This request retrieves first name, last_name, email and role of the User specified in the request.

.. http:get:: /api/user/<email>

   :param string email: Email of the User

   :returns:
      * **success** `(string)` -- Returns 'True' if data is retrieved successfully otherwise 'False'
      * **first_name** `(string)` -- First Name of the User
      * **last_name** `(string)` -- Last Name of the User
      * **email** `(string)` --  Email of the User
      * **role** `(string)` --  role of the User


   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)


.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/user/newuser@gmail.com

      Accept: application/json; charset=utf-8

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {   "success": "True",
            "first_name": "New"
            "last_name":"User",
            "email":"newuser@gmail.com",
            "role":"super"
      }

    **Example response** (for failure):

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "False",
        "error": " User does not exist"
      }

Remove User
***********

This request deletes the requested User from Building Depot.Only the Super user can delete the User in BuildingDepot.

.. http:delete:: /api/user/<email>


   :param string email: email of the User

   :returns:
      * **success** `(string)` -- Returns 'True' if the User is successfully deleted otherwise 'False'

   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      DELETE /api/User/newuser@gmail.com
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
        "error": " User does not exist"
      }
