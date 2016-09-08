.. DataService API Documentation


Usergroups
##########

Usergroups are as the name suggests a group of users formed using the id's with which they are registered in BuildingDepot. Usergroups when combined with SensorGroups help in bringing about the Access Control functions that BuildingDepot provides.

Create UserGroup
******************

This request creates a new UserGroup with the name and description as specified by the user.

.. http:post:: /api/user_group

   :param string name: Name of UserGroup
   :param string description (optional): Descrption for UserGroup
   :returns:
      * **success** `(string)` -- Returns 'True' if data is posted succesfully otherwise 'False'
      * **error** `(string)` -- An additional value that will be present only if the request fails specifying the cause for failure
   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/user_group

      {
        "name": "Test User Group",
        "description": "Description for User Group"
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
        "error": "No Name"
      }

Add users to UserGroup
**********************

This request adds the users specified in the request to the usergroup

Note: The list of user id's sent in this request will overwrite the previous list

.. http:post:: /api/user_group/<name>/users

   :param string name: Name of UserGroup
   :JSON Parameters:
      * **data** `(list)` -- List of user ID's
   :returns:
      * **success** `(string)` -- Returns 'True' if data is posted succesfully otherwise 'False'
      * **error** `(string)` -- An additional value that will be present only if the request fails specifying the cause for failure
   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/user_group/Test/users
      Accept: application/json; charset=utf-8

      {
        "data":[
                 "synergy@gmail.com",
                 "test@gmail.com"
               ]
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
        "error": "One or more users not registered"
      }


Get list of users in UserGroup
******************************

This request retrieves the list of users that are in the specified UserGroup

.. http:get:: /api/user_group/<name>/users

   :param string name: Name of user group (compulsory)
   :returns:
      * **users** `(list)` -- Contains the list of users in this UserGroup

   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /api/user_group/Test/users
      Accept: application/json; charset=utf-8

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "users": [
                   "synergy@gmail.com",
                   "test@gmail.com",
                 ]
      }