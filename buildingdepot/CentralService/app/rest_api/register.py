from . import tagtype
from . import buildingtemplate
from . import building
from . import building_tags
from . import dataservice
from . import ds_buildings
from . import ds_admins
from . import user

def register_view(app_obj):
    tagtype_view = tagtype.TagTypeService.as_view('tagtype_api')
    app_obj.add_url_rule('/api/tagtype',view_func=tagtype_view,methods=['POST'])
    app_obj.add_url_rule('/api/tagtype/<name>',view_func=tagtype_view,methods=['GET','DELETE'])

    template_view = buildingtemplate.BuildingTemplateService.as_view('template_api')
    app_obj.add_url_rule('/api/template',view_func=template_view,methods=['POST'])
    app_obj.add_url_rule('/api/template/<name>',view_func=template_view,methods=['GET','DELETE'])

    building_view = building.BuildingService.as_view('building_api')
    app_obj.add_url_rule('/api/building',view_func=building_view,methods=['POST'])
    app_obj.add_url_rule('/api/building/<name>',view_func=building_view,methods=['GET','DELETE'])

    building_tags_view = building_tags.BuildingTagsService.as_view('building_tags_api')
    app_obj.add_url_rule('/api/building/<building_name>/tags',view_func=building_tags_view,methods=['POST','GET','DELETE'])

    dataservice_view = dataservice.DataserviceService.as_view('dataservice_api')
    app_obj.add_url_rule('/api/dataservice',view_func=dataservice_view,methods=['POST'])
    app_obj.add_url_rule('/api/dataservice/<name>',view_func=dataservice_view,methods=['GET','DELETE'])

    ds_buildings_view = ds_buildings.DataserviceBuildingsService.as_view('ds_buildings_api')
    app_obj.add_url_rule('/api/dataservice/<name>/buildings',view_func=ds_buildings_view,methods=['POST','GET','DELETE'])

    ds_admins_view = ds_admins.DataserviceAdminService.as_view('ds_admins_api')
    app_obj.add_url_rule('/api/dataservice/<name>/admins',view_func=ds_admins_view,methods=['POST','GET','DELETE'])

    users_view = user.UserService.as_view('users_api')
    app_obj.add_url_rule('/api/user',view_func=users_view,methods=['POST'])
    app_obj.add_url_rule('/api/user/<name>',view_func=users_view,methods=['GET','DELETE'])