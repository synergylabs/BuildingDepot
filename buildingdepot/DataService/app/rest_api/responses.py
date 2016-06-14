"""
DataService.rest_api.responses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All the constants i.e.  the responses that will be returned
to the user under certain failure and success conditions are
defined here in this file

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

success_true = {'success':'True'}
missing_data = {'success':'False','error':'Missing data'}
missing_parameters = {'success':'False','error':'Missing parameters'}
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
resolution_high = {'success': 'False', 'error': 'Too many points for this resolution'}
usergroup_add_authorization = {'success': 'False', 'error':'Not authorized for adding users to user group'}
user_not_registered = {'success': 'False', 'error':'One or more users not registered'}
invalid_tagtype = {'success':'False','error':'Invalid tagtype specified'}
invalid_tag_value = {'success':'False','error':'Invalid tag value specified'}
invalid_tag_permission  = {'success':'False','error':'Tag value cannot be used for permissions'}