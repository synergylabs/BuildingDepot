Data Service
###########

The DataService is the service with which users will be interacting directly most of the time. It's within the DataService that all the data related to sensors and the timeseries data of each sensor resides. All the access control related functionality is defined and enforced within the DataService. OAuth access tokens which are required by every query that is sent to BuildingDepot are also generated via the DataService. A brief explanation will be provided here of each of the options available in the DataService.

Sensor
******

Individual sensor points are defined here. After adding a sensor a UUID is generated which will be the unqiue identifier used in all further transactions with BuildingDepot whether it be reading a datapoint from a sensor or posting a bunch of datapoints to a sensor. Each sensor can also have a set of tags attached to it that not only help in categorising them in a meaningful way but also are critical for defining the access control lists later on. The option to attach metadata that is specific to this sensor is also provided. Sensors can be searched for using either the tags or metadata as a filter.

Sensor Group
************

Sensor groups are as the name suggests a set of sensors that have been grouped together on the basis of the tags that the user selected while creating the group. While creating a Sensor groups each individual sensor that the user wants to put in the group do not have to be manuall addded. Simply selecting the tag will automatically add at the backend all the sensors containing that tag into this group. 

User Group
***********

Similar to Sensor groups, User groups are a list of users that have been categorised into one group. Groups are created using the user email id that was used during registration.

Permission
***********

In the permissions section Sensor groups and User groups come together to form the access control lists. Here we select a User Group and a Sensor Group and a permission value with which we want to associate these both. There are three levels of permission defined in BuildingDepot which are 'd/r' (deny read) ,'r' (read) and 'r/w' (read write). If there are multiple permissison mappings between a user and a sensor then the one that is most restrictive is chosen. 

OAuth
*****

To generate an OAuth token a client id and client secret key are required. These are generated within the DataService by the user through the GUI. These values will be valid until the user regenerates them for that certain account. The process to generate an OAuth token after these values have been obtained is defined in the REST API Documentation.