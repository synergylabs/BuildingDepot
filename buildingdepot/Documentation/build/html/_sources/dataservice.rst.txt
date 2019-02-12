Data Service
############

The DataService is the service with which users will be interacting directly most of the time. It's within the DataService that all the data related to sensors and the timeseries data of each sensor resides. All the access control related functionality is defined and enforced within the DataService. OAuth access tokens which are required by every query that is sent to BuildingDepot are also generated via the DataService. A brief explanation will be provided here of each of the options available in the DataService.

Sensor
******

Individual sensor points are defined here. After adding a sensor a UUID is generated which will be the unique identifier used in all further transactions with BuildingDepot whether it be reading a datapoint from a sensor or posting a bunch of datapoints to a sensor. Each sensor can also have a set of tags attached to it that not only help in categorising them in a meaningful way but also are critical for defining the access control lists later on. The option to attach metadata that is specific to this sensor is also provided. Sensors can be searched for using either the tags or metadata as a filter.
