.. DataService API Documentation

===============
REST API's
===============

All urls in this chapter are with respect to the base url of the DataService. For example: If the DataService is at http://www.example.com:82 then a url such as /service/sensor refers to http://www.example.com:82/service/sensor

Authentication
--------------

In order to access the DataService all users will first have to generate an OAuth Token using the Client ID and secret Client Key that they obtain from their account at the DataService. Once logged into the DataService users can go to the OAuth tab and generate a Client ID and Key that should never be shared with any other users.

Once these have been generated the user can request BuildingDepot for the access token and refresh token. The access token will be valid for the next 24 hours after which another will have to be generated using the refresh token. The OAuth token should also never be shared publicly.

This OAuth token will have to be sent in the headers of all the requests made to BuildingDepot.

.. HTTPS
.. -----

.. In order to ensure security, all requests must go through HTTPS.


.. toctree::
   :maxdepth: 2

   sensor.rst
   sensordata.rst
   metadata.rst
   tags.rst
   usergroup.rst
   sensorgroup.rst
   permission.rst
   oauth.rst

.. may be needed for html generation
.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`