.. DataService API Documentation

================
DataService APIs
================

All urls in this chapter are with respect to the base url of the DataService. For example: If the DataService is at http://www.example.com:82 then a url such as /service/sensor refers to http://www.example.com:82/service/sensor

Authentication
--------------

In order to access the DataService all users will first have to generate an OAuth Token using the Client ID and secret Client Key that they obtain from their account at the Central Service. Once logged into the CentralService users can go to the OAuth tab and generate a Client ID and Key that should never be shared with any other users.

Once the Client ID and Key have been generated the user can request BuildingDepot for the access token. The access token will be valid for the next 24 hours after which another access token will have to be generated.The OAuth token should also never be shared publicly.

This OAuth token will have to be sent in the headers of all the requests made to BuildingDepot.

.. HTTPS
.. -----

.. In order to ensure security, all requests must go through HTTPS.


.. toctree::
   :maxdepth: 2

   ../CentralService/oauth.rst
   sensordata.rst
   pubsub.rst


.. may be needed for html generation
.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
