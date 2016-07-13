from .buildings import tagtype,buildingtemplate,building,building_tags
from .dataservices import dataservice,ds_buildings,ds_admins
from .users import user
from .sensorgroups import sensorgroup,sg_tags
from .usergroups import ug_users,usergroup
from .sensors import sensor,search,sensor_tags,metadata
from .permissions import permission

def register_view(app_obj):
    sensor_view = sensor.SensorService.as_view('sensor_api')
    app_obj.add_url_rule('/api/sensor/<name>',view_func=sensor_view,methods=['GET'])
    app_obj.add_url_rule('/api/sensor',view_func=sensor_view,methods=['POST'])

    metadata_view = metadata.MetaDataService.as_view('metadata_api')
    app_obj.add_url_rule('/api/sensor/<name>/metadata',view_func=metadata_view,methods=['GET','POST'])

    sensortags_view = sensor_tags.SensorTagsService.as_view('sensortags_api')
    app_obj.add_url_rule('/api/sensor/<name>/tags',view_func=sensortags_view,methods=['GET','POST'])

    sensorgroup_view = sensorgroup.SensorGroupService.as_view('sensorgroup_api')
    app_obj.add_url_rule('/api/sensor_group',view_func=sensorgroup_view,methods=['POST'])
    app_obj.add_url_rule('/api/sensor_group/<name>',view_func=sensorgroup_view,methods=['GET'])

    sgtags_view = sg_tags.SensorGroupTagsService.as_view('sgtags_api')
    app_obj.add_url_rule('/api/sensor_group/<name>/tags',view_func=sgtags_view,methods=['GET','POST'])

    usergroup_view = usergroup.UserGroupService.as_view('usergroup_api')
    app_obj.add_url_rule('/api/user_group',view_func=usergroup_view,methods=['POST'])
    app_obj.add_url_rule('/api/user_group/<name>',view_func=usergroup_view,methods=['GET'])

    ugusers_view = ug_users.UserGroupUsersService.as_view('ugusers_api')
    app_obj.add_url_rule('/api/user_group/<name>/users',view_func=ugusers_view,methods=['GET','POST'])

    permission_view = permission.PermissionService.as_view('permission_service')
    app_obj.add_url_rule('/api/permission',view_func=permission_view,methods=['GET','POST','DELETE'])

    search_view = search.SearchService.as_view('search_service')
    app_obj.add_url_rule('/api/search',view_func=search_view,methods=['POST'])

    tagtype_view = tagtype.TagTypeService.as_view('tagtype_api')
    app_obj.add_url_rule('/api/tagtype', view_func=tagtype_view, methods=['POST'])
    app_obj.add_url_rule('/api/tagtype/<name>', view_func=tagtype_view, methods=['GET', 'DELETE'])

    template_view = buildingtemplate.BuildingTemplateService.as_view('template_api')
    app_obj.add_url_rule('/api/template', view_func=template_view, methods=['POST'])
    app_obj.add_url_rule('/api/template/<name>', view_func=template_view, methods=['GET', 'DELETE'])

    building_view = building.BuildingService.as_view('building_api')
    app_obj.add_url_rule('/api/building', view_func=building_view, methods=['POST'])
    app_obj.add_url_rule('/api/building/<name>', view_func=building_view, methods=['GET', 'DELETE'])

    building_tags_view = building_tags.BuildingTagsService.as_view('building_tags_api')
    app_obj.add_url_rule('/api/building/<building_name>/tags', view_func=building_tags_view,
                         methods=['POST', 'GET', 'DELETE'])

    dataservice_view = dataservice.DataserviceService.as_view('dataservice_api')
    app_obj.add_url_rule('/api/dataservice', view_func=dataservice_view, methods=['POST'])
    app_obj.add_url_rule('/api/dataservice/<name>', view_func=dataservice_view, methods=['GET', 'DELETE'])

    ds_buildings_view = ds_buildings.DataserviceBuildingsService.as_view('ds_buildings_api')
    app_obj.add_url_rule('/api/dataservice/<name>/buildings', view_func=ds_buildings_view,
                         methods=['POST', 'GET', 'DELETE'])

    ds_admins_view = ds_admins.DataserviceAdminService.as_view('ds_admins_api')
    app_obj.add_url_rule('/api/dataservice/<name>/admins', view_func=ds_admins_view, methods=['POST', 'GET', 'DELETE'])

    users_view = user.UserService.as_view('users_api')
    app_obj.add_url_rule('/api/user', view_func=users_view, methods=['POST'])
    app_obj.add_url_rule('/api/user/<name>', view_func=users_view, methods=['GET', 'DELETE'])
