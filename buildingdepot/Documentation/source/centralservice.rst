Central Service
############

The Central Service within BuildingDepot is the part of the system that holds all the core metadata. Starting from the structures of the Buildings to the DataServices that lie in an installation the CentralService plays a very important role in organising the data within BuildingDepot in a meaningful way. A brief explanation will be provided here of each of the options available in the CentralService.

TagType
****************

Tags are an integral part of BuildingDepot and play an important role in organising and categorising the sensors and their data. Users can create new tags here which will be used in various places throughout BuildingDepot. When creating each tag parent tag(s) can be specified for each tag enabling us to create a tag hierarchy that proves to be very useful when defining structures such as Buildings. Here only the tag names are specified and the values for these tags are specified later on. Each tag can have multiple values if needed.

BuildingTemplate
*****************

Each building within BuildingDepot has a BuildingTemplate as a foundation. The BuildingTemplate helps define the structure of the building. The user has to assign a set of tags to the BuildingTemplate on creation which can be used later on for all the sensors within that building.

Building
**********

All the buildings that are present within the deployment of BuildingDepot are defined here. When adding a new building a BuildingTemplate has to be selected which defines the structure of this building. The tags that are available to be assigned to this building are dependent on the BuildingTemplate. Tags can be selected and the values for each of them can be specified here. Each tag can have multiple values specified for it.

Data Services
**************

BuildingDepot consists of a single CentralService and if needed multiple DataServices. The number of DataServices to deploy is a decision that is completely left to the user. A DataService per building is an ideal choice that we suggest. Each DataService has to be specified within the DataService's section in the CentralService. For each DataService all the buildings that belong to it also have to be selected and added. The admins for each DataService who will have complete adminstrative control over this DataService also have to be specified here. 

Note: The first DataService has to be called "ds1".