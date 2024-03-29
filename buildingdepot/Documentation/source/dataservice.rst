.. image:: images/BuildingDepot.svg
   :width: 800

Data Service
############

The DataService is the service with which users will be interacting directly most of the time. It's within the DataService that all the data related to sensors and the timeseries data of each sensor resides. All the access control related functionality is defined and enforced within the DataService. OAuth access tokens which are required by every query that is sent to BuildingDepot are also generated via the DataService. A brief explanation will be provided here of each of the options available in the DataService.

DataService stores point time series data points from the underlying point networks. The
DataService manages the points and time series data points of points allocated to it. A
DataService may belong to any single administrative group that requires sole control over who
can access the underlying point data. Different buildings on a campus might desire their own
DataService. Thus it is up to an institution to determine how many DataServices are needed
depending on the specific groups that exist and their needs.

DataService needs to query CentralService for user accounts, building tags and permission
information. The communication is immensely frequent as almost every request to DataService
needs user authentication and permission check. Therefore, only keeping a single
CentralService would be a performance bottleneck. To resolve this issue, we set up the
CentralService in a master­slave mode. The master CentralService only accepts write requests
and each of its replicas undertakes read requests from a single DataService. In this way, the
request traffic load can be balanced on all replicas.

.. image:: images/DSComponents.svg
   :width: 800

Sensor
******

The time-series data of all the points in buildings associated with the Data Service is stored here. The sensor UUID(s) are used in all further time-series transactions with BuildingDepot whether it be reading a datapoint from a sensor or posting a bunch of datapoints to a sensor.The time-series data of all the points in buildings associated with a certain Data Service is stored here. The sensor UUID(s) are used in all further time-series transactions with BuildingDepot whether it be reading a datapoint from a sensor or posting a bunch of datapoints to a sensor.

Apps
******

BuildingDepot allows users to subscribe to sensors' time-series data. This can be done by registering a new app and associating it with the desired sensor UUIDs. All the information about a user's apps is located here.