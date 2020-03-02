.. image:: images/GIOTTO.svg
   :width: 800

Central Service
###############

The Central Service within BuildingDepot is the part of the system that holds all the core metadata. Starting from the structures of the Buildings to the DataServices that lie in an installation the CentralService plays a very important role in organising the data within BuildingDepot in a meaningful way. A brief explanation will be provided here of each of the options available in the CentralService.

OAuth
*****

To generate an OAuth token a client id and client secret key are required. These are generated within the DataService by the user through the GUI. These values will be valid until the user regenerates them for that certain account. The process to generate an OAuth token after these values have been obtained is defined in the REST API Documentation.

TagType
*******

Tags are an integral part of BuildingDepot and play an important role in organising and categorising the sensors and their data. Users can create new tags here which will be used in various places throughout BuildingDepot. When creating each tag parent tag(s) can be specified for each tag enabling us to create a tag hierarchy that proves to be very useful when defining structures such as Buildings. Here only the tag names are specified and the values for these tags are specified later on. Each tag can have multiple values if needed.

BuildingTemplate
****************

Each building within BuildingDepot has a BuildingTemplate as a foundation. The BuildingTemplate helps define the structure of the building. The user has to assign a set of tags to the BuildingTemplate on creation which can be used later on for all the sensors within that building.

Building
********

All the buildings that are present within the deployment of BuildingDepot are defined here. When adding a new building a BuildingTemplate has to be selected which defines the structure of this building. The tags that are available to be assigned to this building are dependent on the BuildingTemplate. Tags can be selected and the values for each of them can be specified here. Each tag can have multiple values specified for it.

Data Services
*************

BuildingDepot consists of a single CentralService and if needed multiple DataServices. The number of DataServices to deploy is a decision that is completely left to the user. A DataService per building is an ideal choice that we suggest. Each DataService has to be specified within the DataService's section in the CentralService. For each DataService all the buildings that belong to it also have to be selected and added. The admins for each DataService who will have complete administrative control over this DataService also have to be specified here.

Note: The first DataService has to be called "ds1".

Sensor
******

Individual sensor points are defined here. After adding a sensor a UUID is generated which will be the unique identifier used in all further transactions with BuildingDepot whether it be reading a datapoint from a sensor or posting a bunch of datapoints to a sensor. Each sensor can also have a set of tags attached to it that not only help in categorising them in a meaningful way but also are critical for defining the access control lists later on. The option to attach metadata that is specific to this sensor is also provided. Sensors can be searched for using either the tags or metadata as a filter.

Sensor Group
************

Sensor groups are as the name suggests a set of sensors that have been grouped together on the basis of the tags that the user selected while creating the group. While creating a Sensor groups each individual sensor that the user wants to put in the group do not have to be manual added. Simply selecting the tag will automatically add at the backend all the sensors containing that tag into this group.

User Group
**********

Similar to Sensor groups, User groups are a list of users that have been categorised into one group. Groups are created using the user email id that was used during registration.

Permission
**********

In the permissions section Sensor groups and User groups come together to form the access control lists. Here we select a User Group and a Sensor Group and a permission value with which we want to associate these both. There are three levels of permission defined in BuildingDepot which are 'd/r' (deny read) ,'r' (read), 'r/w' (read write) and 'r/w/p' (read write permission). If there are multiple permission mappings between a user and a sensor then the one that is most restrictive is chosen.
