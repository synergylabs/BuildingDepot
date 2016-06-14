from . import views
from . import sensor
from . import timeseries
from . import metadata
from . import sensor_tags
from . import sensorgroup
from . import sg_tags
from . import ug_users
from . import usergroup
from . import apps
from . import app_subscription
from . import permission
from . import search
from .. import oauth


def register_view(app_obj):
    sensor_view = sensor.SensorService.as_view('sensor_api')
    app_obj.add_url_rule('/api/sensor/<name>',view_func=sensor_view,methods=['GET'])
    app_obj.add_url_rule('/api/sensor',view_func=sensor_view,methods=['POST'])

    metadata_view = metadata.MetaDataService.as_view('metadata_api')
    app_obj.add_url_rule('/api/sensor/<name>/metadata',view_func=metadata_view,methods=['GET','POST'])

    sensortags_view = sensor_tags.SensorTagsService.as_view('sensortags_api')
    app_obj.add_url_rule('/api/sensor/<name>/tags',view_func=sensortags_view,methods=['GET','POST'])

    timeseries_view = timeseries.TimeSeriesService.as_view('timeseries_api')
    app_obj.add_url_rule('/api/sensor/<name>/timeseries',view_func=timeseries_view,methods=['GET'])
    app_obj.add_url_rule('/api/sensor/timeseries',view_func=timeseries_view,methods=['POST'])

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

    app_view = apps.AppService.as_view('app_api')
    app_obj.add_url_rule('/api/apps',view_func=app_view,methods=['GET','POST'])

    appsub_view = app_subscription.AppSubscriptionService.as_view('appsub_api')
    app_obj.add_url_rule('/api/apps/subscription',view_func=appsub_view,methods=['POST','DELETE'])

    permission_view = permission.PermissionService.as_view('permission_service')
    app_obj.add_url_rule('/api/permission',view_func=permission_view,methods=['GET','POST','DELETE'])

    search_view = search.SearchService.as_view('search_service')
    app_obj.add_url_rule('/api/search',view_func=search_view,methods=['POST'])