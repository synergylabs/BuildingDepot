.. DataService API Documentation

===============
CentalService API
===============

All urls in this chapter are with respect to the base url of the CentralService. For example: If the CentralService is at http://www.example.com:82 then a url such as /service/tagtype refers to http://www.example.com:82/central/tagtype account.

Authentication
--------------

In order to access the CentralService all users will first have to generate an OAuth Token using the Client ID and secret Client Key that they obtain from their account at the CentralService. Once logged into the CentralService users can go to the OAuth tab and generate a Client ID and Key that should never be shared with any other users.

Once these have been generated the user can request BuildingDepot for the access token and refresh token. The access token will be valid for the next 24 hours after which another will have to be generated using the refresh token. The OAuth token should also never be shared publicly.

This OAuth token will have to be sent in the headers of all the requests made to BuildingDepot.

TagType
--------

Tags play a very crucial role within BuildingDepot in defining permissions that restrict access to sensors based on the permissions a user has. They help in categorising sensors that can be easily allocated in groups to different users. Tags can be defined in the CentralService at http://www.example.com:82/central/tagtype. Tags have a hierarchical structure i.e. a tag can have both parent tags and children tags. This proves to be very helpful when definig building structures.
                 
.. HTTPS
.. -----

.. In order to ensure security, all requests must go through HTTPS. 


.. toctree::
   :maxdepth: 2
   
   api_index.rst
   admin.rst
   subscriber.rst
   sensor.rst
   sensordata.rst
   sensor_context.rst
   sensorpoint_type.rst
   sensor_template.rst
   sensor_group.rst
   sensor_network.rst
   permission.rst
   keyword.rst
   context.rst

.. may be needed for html generation
.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
