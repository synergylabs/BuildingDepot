"""
CentralService.rest_api.responses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All the constants i.e.  the responses that will be returned
to the user under certain failure and success conditions are
defined here in this file

@copyright: (c) 2021 SynergyLabs
@license: CMU License. See License file for details.
"""

# common responses
success_true = {"success": "True"}
missing_data = {"success": "False", "error": "Missing data"}
missing_parameters = {"success": "False", "error": "Missing parameters"}
invalid_building = {"success": "False", "error": "Building does not exist"}
ds_error = {"success": "False", "error": "Communication failure with DataService"}

# user-related responses:
inactive_user = {
    "success": "False",
    "error": "The user you are attempting to interact with is not active",
}

# building API common responses:
invalid_tagtype = {"success": "False", "error": "TagType does not exist"}
invalid_template = {"success": "False", "error": "BuildingTemplate does not exist"}
tagtype_referenced = {
    "success": "False",
    "error": "This tag value is being referenced, cannot delete",
}
# building API specific responses:
#   building post/get/deletion API responses
building_in_use = {"success": "False", "error": "Building is in use"}
#   building-tags post/get/deletion API responses
invalid_parents = {
    "success": "False",
    "error": "One of the parent tags specified does not exist",
}
invalid_tag_value = {"success": "False", "error": "Tag value does not exist"}
#   building-template post/get/deletion API responses
invalid_tagtypes = {"success": "False", "error": "One of the tagtypes does not exist"}
tagtype_in_use = {
    "success": "False",
    "error": "Tagtype is in use, cannot be removed from template",
}
template_in_use = {"success": "False", "error": "BuildingTemplate is in use"}
#   building-tagtype post/get/deletion API responses
invalid_parent_tags = {"success": "False", "error": "List of parents tags not valid"}

# data-service API common responses
invalid_dataservice = {"success": "False", "error": "DataService does not exist"}
# dataservice API specific responses:
#   data-service post/get/deletion API responses
dataservice_in_use = {
    "success": "False",
    "error": "Cannot delete DataService, contains buildings",
}
#   ds-admin post/get/deletion API responses
ds_invalid_admin = {"success": "False", "error": "One of the users does not exist"}
#   ds-building post/get/deletion API responses
ds_invalid_building = {
    "success": "False",
    "error": "One of the buildings does not exist",
}

# ACL permissions API responses:
permission_not_allowed = {
    "success": "False",
    "error": "Not authorized to create permissions for the specified SensorGroup tags",
}
no_permission = {"success": "False", "error": "Permission does not exist"}
no_usergroup = {"success": "False", "error": "User group does not exist"}
no_sensorgroup = {"success": "False", "error": "Sensor group does not exist"}
no_permission_val = {"success": "False", "error": "Permission value does not exist"}
permission_authorization = {
    "success": "False",
    "error": "Not authorized to modify this permission",
}
permission_not_defined = {"success": "False", "error": "Permission is not defined"}
permission_del_authorization = {
    "success": "False",
    "error": "Not authorized to delete this permission",
}
permission_modify_authorization = {
    "success": "False",
    "error": "Not authorized to modify this permission",
}
permission_invalid_setting = {
    "success": "False",
    "error": "Invalid permission setting value",
}
no_permission_id = {
    "success": "False",
    "error": "User does not have an ID to begin listening for permission requests",
}

# SensorGroup API responses
sensorgroup_exists = {"success": "False", "error": "Sensorgroup already exists"}
no_sensorgroup_tags = {
    "success": "False",
    "error": "Cannot create permissions for a SensorGroup with no tags",
}
invalid_sensorgroup = {"success": "False", "error": "Sensorgroup does not exist"}
sensorgroup_used = {
    "success": "False",
    "error": "Sensor group tags cannot be edited. Already being used for "
    "permissions",
}
invalid_tag_permission = {
    "success": "False",
    "error": "Tag value cannot be used for permissions",
}
sensorgroup_delete_authorization = {
    "success": "False",
    "error": "Not authorized to delete Sensorgroup",
}

# Sensors API responses
no_search_parameters = {"success": "False", "error": "No search parameters specified"}
invalid_uuid = {"success": "False", "error": "Sensor does not exist"}

# UserGroup API responses
invalid_usergroup = {"success": "False", "error": "Usergroup does not exist"}
usergroup_add_authorization = {
    "success": "False",
    "error": "Not authorized for adding users to user group",
}
user_not_registered = {"success": "False", "error": "One or more users not registered"}
usergroup_exists = {"success": "False", "error": "Usergroup already exists"}
usergroup_delete_authorization = {
    "success": "False",
    "error": "Not authorized to delete user group",
}

# User creation API responses
unauthorized_user_lookup = {
    "success": "False",
    "error": "Not authorized to get information on this user",
}
invalid_user_role = {
    "success": "False",
    "error": "User role should be either default or super",
}
invalid_user = {"success": "False", "error": "User does not exist"}
user_exists = {"success": "False", "error": "User already exists"}
super_user_required = {
    "success": "False",
    "error": "Super user privileges required. Not authorized for this " "operation",
}

# RabbitMQ error responses
rabbit_mq_bind_error = {
    "success": "False",
    "error": "Unable to bind rabbitmq queue. Check params are valid",
}

# Notification error responses
client_id_already_exists = {
    "success": "False",
    "error": "The user already has a client notification ID",
}

# not used
missing_template = {"success": "False", "error": "Template is not specified"}
tagtype_name_change_invalid = {
    "success": "False",
    "error": "Cannot change name as TagType is already in use",
}
acl_tag_superuser = {
    "success": "False",
    "error": "Super user privileges required. Not authorized to change "
    "the usage of this tag",
}
registration_email = """From: Admin <%s>
To: %s <%s>
Subject: Password for BuildingDepot account

Account details:
User id : %s
Password : %s
Hostname: %s

Please register and change your password immediately.
"""
