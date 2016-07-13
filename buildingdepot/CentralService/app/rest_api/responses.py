"""
CentralService.rest_api.responses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All the constants i.e.  the responses that will be returned
to the user under certain failure and success conditions are
defined here in this file

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

success_true = {'success': 'True'}
missing_data = {'success': 'False', 'error': 'Missing data'}
missing_parameters = {'success': 'False', 'error': 'Missing parameters'}
invalid_tagtypes = {'success': 'False', 'error': 'One of the tagtypes doesn\'t exist'}
invalid_tagtype = {'success': 'False', 'error': 'TagType doesn\'t exist'}
invalid_template = {'success': 'False', 'error': 'BuildingTemplate doesn\'t exist'}
invalid_parent_tags = {'success': 'False', 'error': 'List of parents tags not valid'}
missing_template = {'success': 'False', 'error': 'Template is not specified'}
template_in_use = {'success': 'False', 'error': 'BuildingTemplate is in use'}
building_in_use = {'success': 'False', 'error': 'Building is in use'}
tagtype_in_use = {'success': 'False', 'error': 'Tagtype is in use, cannot be removed from template'}
tagtype_name_change_invalid = {'success': 'False', 'error': 'Cannot change name as TagType is already in use'}
invalid_building = {'success': 'False', 'error': 'Building doesn\'t exist'}
invalid_parents = {'success': 'False', 'error': 'One of the parent tags specified doesn\'t exist'}
tagtype_referenced = {'success': 'False', 'error': 'This tag value is being referenced, cannot delete.'}
invalid_tag_value = {'success': 'False', 'error': 'Tag value doesn\'t exist.'}
invalid_dataservice = {'success': 'False', 'error': 'DataService doesn\'t exist'}
dataservice_in_use = {'success': 'False', 'error': 'Cannot delete DataService, contains buildings.'}
ds_invalid_building = {'success': 'False', 'error': 'One of the buildings doesn\'t exist'}
ds_invalid_admin = {'success': 'False', 'error': 'One of the users doesn\'t exist'}
unauthorized_user = {'success': 'False', 'error': 'You are not authorized to create a super user'}
invalid_user = {'success': 'False', 'error': 'User doesn\'t exist'}
user_exists = {'success': 'False', 'error': 'User already exists.'}
super_user_required = {'success': 'False','error': 'Super user privileges required. You are not authorized for this operation'}
acl_tag_superuser = {'success': 'False','error': 'Super user privileges required. You are not authorized to change the usage of this tag'}
no_permission = {'success': 'False', 'error': 'Permission doesn\'t exist'}
no_permission_val =  {'success': 'False', 'error': 'Permission value doesn\'t exist'}
permission_authorization = {'success':'False','error':'You are not authorized to modify this permission'}
permission_not_defined = {'success': 'False', 'error': 'Permission is not defined'}
permission_del_authorization = {'success':'False','error': 'You are not authorized to delete this permisson'}
no_usergroup = {'success': 'False', 'error': 'User group doesn\'t exist'}
no_sensorgroup = {'success': 'False', 'error': 'Sensor group doesn\'t exist'}
invalid_uuid = {'success': 'False', 'error': 'Sensor doesn\'t exist'}
invalid_building = {'success': 'False', 'error': 'Building does not exist'}
invalid_sensorgroup = {"success":"False","error":"Sensorgroup doesn't exist"}
invalid_usergroup = {"success":"False","error":"Usergroup doesn't exist"}
sensorgroup_exists = {'success':'False','error':'Sensorgroup already exists'}
usergroup_exists = {'success':'False','error':'Usergroup already exists'}
sensorgroup_used = {'success': 'False', 'error': 'Sensor group tags cannot be edited. Already being used for permissions'}
usergroup_add_authorization = {'success': 'False', 'error':'Not authorized for adding users to user group'}
user_not_registered = {'success': 'False', 'error':'One or more users not registered'}
invalid_tagtype = {'success':'False','error':'Invalid tagtype specified'}
invalid_tag_value = {'success':'False','error':'Invalid tag value specified'}
invalid_tag_permission  = {'success':'False','error':'Tag value cannot be used for permissions'}
no_search_parameters = {'success':'False','error':'No search parameters specified'}
ds_error = {'success':'False','error':'Communication failure with DataService'}

registration_email = """From: Admin <%s>
To: %s <%s>
Subject: Password for BuildingDepot account

Account details:
User id : %s
Password : %s

Please register and change your password immediately.
"""
