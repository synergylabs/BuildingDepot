.. image:: images/BuildingDepot.svg
   :width: 800

Central Service
###############

The Central Service within BuildingDepot is the part of the system that holds all the core metadata. Starting from the structures of the Buildings to the DataServices that lie in an installation the CentralService plays a very important role in organising the data within BuildingDepot in a meaningful way. A brief explanation will be provided here of each of the options available in the CentralService.

We define any entity to which a timeseries can be associated with as a Point. A Point can be
measurements from sensors, or commands to turn a light on/off, or a configuration parameter
such as cycle type in a washing machine or even a fault indicator. This includes both real­world
sensors/actuators, as well as virtual sensors/actuators created in the Central Service as
abstractions of RealWorld sensors/actuators (such as a ‘building average temperature sensor’).
Virtual and RealWorld points are treated identically within the CentralService, with differences
occurring at the level of connectors (see Connectors document for interfacing between the
CentralService and sensors). In BuildingDepot, each point is given a UUID (universally unique ID) and
metadata is associated with it using tags.

Tags are key value pairs associated with a point. For example, an office temperature sensor
would be associated with tags like “Room = 300”, “Type = Temperature Sensor”, “Unit =
Fahrenheit” and so on. Tags themselves can refer to complex entities and be associated with
other tags. For example, Room 300 can be associated with its metadata such as area and
usage type . Tags form the core of BuildingDepot metadata, and are used for searching and defining permissions.

BuildingDepot supports pre­defined tag types that acts as a template for a user to start tagging entities
in a building. These templates are provided to support standard naming convention, such as the
tags defined by Project Haystack2. These tags are also used as the key search mechanism
within BuildingDepot. Using REST APIs, users can query for individual entities based on single tag
(such as a Room = 300) or based on more complex combinations of tags (Room = 300 and
Type = Occupancy and Building = Example_Building). All entities which meet the requirements
of the search are returned as JSON objects which contain their UUID, tags, and Metadata.
In addition to tags on entities, BuildingDepot also utilizes context based tags for Users. Depending on
how a user logs in (e.g. with or without admin privileges) they will have a context tag added to
determine the privileges that they enjoy (user credentials). Users groups are created by
assigning a user­group tag to each user which is part of the group. This is of particular
importance later when determining permissions.

In addition to User Groups, Sensor groups are as the name suggests a set of points that have
been grouped together on the basis of the tags that the user selected while creating the group.
While creating a Sensor group each individual points that the user wants to put in the group do
not have to be manually added. Simply selecting the tag will automatically add at the backend
all the points containing that tag into this group.
Sensor groups and User groups come together to form the access control lists. Access control
lists are a key element in BuildingDepot to facilitate both privacy and security. For pairs of User
Groups and Sensor Groups, we choose a permission value with which we want to associate.
There are four levels of permission defined in BuildingDepot which are ‘d/r’ (deny read) ,’r’ (read) , ‘r/w’
(read write) and ‘r/w/p’ (read write permission). If there are multiple permission mappings
between a user and a point then the one that is most restrictive is chosen. The deny read
permission level, in particular, is important for maintaining privacy of data for various groups
simultaneously using BuildingDepot for a building.

When a r/w/p permission link is created between the UserGroup “Home_usergroup” and Sensor
Group “Home”. All users in UserGroup get r/w/p access to points in SensorGroup. Any user can
create any permission link that they want but the set of points that the users in the UserGroup
get access to in the SensorGroup that they have been given permission to will depend on the
user that has created the permission. Only the points that the creator of this permission has
r/w/p access to will be the points that the users will gain access to based on this permission link.

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
