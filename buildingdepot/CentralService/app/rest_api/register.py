from .buildings import building, building_tags
from .buildingtemplate import buildingtemplate, buildingtemplate_tagtypes
from .dataservices import dataservice, ds_buildings, ds_admins
from .notifications import notification
from .permissions import permission, permission_request, permission_uuid
from .sensorgroups import sensorgroup, sg_tags
from .sensors import sensor, search, sensor_tags, sensor_views
from .tagtype import tagtype
from .usergroups import ug_users, usergroup
from .users import user


def register_view(app_obj):
    tagtype_view = tagtype.TagTypeService.as_view("tagtype_api")
    # add/change tagtypes
    app_obj.add_url_rule("/api/tagtype", view_func=tagtype_view, methods=["POST"])
    # get info regarding a tagtype, delete a tag type
    app_obj.add_url_rule(
        "/api/tagtype/<name>", view_func=tagtype_view, methods=["GET", "DELETE"]
    )

    template_view = buildingtemplate.BuildingTemplateService.as_view("template_api")
    # post creates/modifies building templates
    # get returns information on a specified building template.
    # delete deletes the template
    app_obj.add_url_rule("/api/template", view_func=template_view, methods=["POST"])
    app_obj.add_url_rule(
        "/api/template/<name>", view_func=template_view, methods=["GET", "DELETE"]
    )

    template_tagtypes_view = buildingtemplate_tagtypes.BuildingTemplateTagtypeService.as_view(
        "template_tagtypes_api"
    )
    # post creates/modifies building templates
    # get returns information on a specified building template.
    # delete deletes the template
    app_obj.add_url_rule(
        "/api/template/<name>/tags",
        view_func=template_tagtypes_view,
        methods=["GET", "DELETE", "POST", "PUT"],
    )

    building_view = building.BuildingService.as_view("building_api")
    # post creates/modifies buildings
    # get returns information on a specified building.
    # delete deletes the building.
    app_obj.add_url_rule("/api/building", view_func=building_view, methods=["POST"])
    app_obj.add_url_rule(
        "/api/building/<name>", view_func=building_view, methods=["GET", "DELETE"]
    )

    building_tags_view = building_tags.BuildingTagsService.as_view("building_tags_api")
    # get a list of tags associated with a specified building
    # post changes/adds tags to a specified building
    # delete removes a tag from a specified building
    app_obj.add_url_rule(
        "/api/building/<building_name>/tags",
        view_func=building_tags_view,
        methods=["POST", "GET", "DELETE"],
    )

    dataservice_view = dataservice.DataserviceService.as_view("dataservice_api")
    # post changes/adds a data service to a central service
    # get returns info on the specified data service
    # delete unregisters a data service from a central service
    app_obj.add_url_rule(
        "/api/dataservice", view_func=dataservice_view, methods=["POST"]
    )
    app_obj.add_url_rule(
        "/api/dataservice/<name>", view_func=dataservice_view, methods=["GET", "DELETE"]
    )

    ds_buildings_view = ds_buildings.DataserviceBuildingsService.as_view(
        "ds_buildings_api"
    )
    # post changes/adds a building to a data service
    # get returns info on buildings registered to the specified data service
    # delete removes a building from a data service
    app_obj.add_url_rule(
        "/api/dataservice/<name>/buildings",
        view_func=ds_buildings_view,
        methods=["POST", "GET", "DELETE"],
    )

    ds_admins_view = ds_admins.DataserviceAdminService.as_view("ds_admins_api")
    # handles interactions between admins in data services
    app_obj.add_url_rule(
        "/api/dataservice/<name>/admins",
        view_func=ds_admins_view,
        methods=["POST", "GET", "DELETE"],
    )

    sensor_view = sensor.SensorService.as_view("sensor_api")
    # get sensor by name
    app_obj.add_url_rule(
        "/api/sensor/<name>", view_func=sensor_view, methods=["GET", "DELETE"]
    )
    # create a new sensor
    app_obj.add_url_rule("/api/sensor", view_func=sensor_view, methods=["POST"])

    sensor_owned_view = sensor.SensorOwnedService.as_view("sensor_owned_api")
    # get all sensors owned and have permission to
    app_obj.add_url_rule("/api/sensor", view_func=sensor_owned_view, methods=["GET"])

    sensor_view_view = sensor_views.SensorViewService.as_view("sensor_view_api")
    # get views of sensor by name
    app_obj.add_url_rule(
        "/api/sensor/<name>/views", view_func=sensor_view_view, methods=["GET"]
    )
    # delete views of sensor by name
    app_obj.add_url_rule(
        "/api/sensor/<name>/views/<uuid>",
        view_func=sensor_view_view,
        methods=["DELETE"],
    )
    # create a new views for sensor
    app_obj.add_url_rule(
        "/api/sensor/<name>/views", view_func=sensor_view_view, methods=["POST"]
    )

    sensortags_view = sensor_tags.SensorTagsService.as_view("sensortags_api")
    # get gets a sensor's tags
    # post changes/adds to a sensor's tags
    app_obj.add_url_rule(
        "/api/sensor/<name>/tags", view_func=sensortags_view, methods=["GET", "POST"]
    )

    sensorgroup_view = sensorgroup.SensorGroupService.as_view("sensorgroup_api")
    # post creates an new sensor group
    app_obj.add_url_rule(
        "/api/sensor_group", view_func=sensorgroup_view, methods=["POST"]
    )
    # get a list of sensors in a specified sensor group
    app_obj.add_url_rule(
        "/api/sensor_group/<name>", view_func=sensorgroup_view, methods=["GET"]
    )
    # delete a sensor_group
    app_obj.add_url_rule(
        "/api/sensor_group/<name>", view_func=sensorgroup_view, methods=["DELETE"]
    )

    sensorgroup_owned_view = sensorgroup.SensorGroupOwnedService.as_view(
        "sensorgroup_owned_api"
    )
    # get all sensor groups owned by the requesting user
    app_obj.add_url_rule(
        "/api/sensor_group", view_func=sensorgroup_owned_view, methods=["GET"]
    )

    sgtags_view = sg_tags.SensorGroupTagsService.as_view("sgtags_api")
    # get a list of tags in a specified sensor group
    # post changes/adds tags to a specified sensor group
    app_obj.add_url_rule(
        "/api/sensor_group/<name>/tags", view_func=sgtags_view, methods=["GET", "POST"]
    )

    usergroup_view = usergroup.UserGroupService.as_view("usergroup_api")
    # post creates a new user group
    app_obj.add_url_rule("/api/user_group", view_func=usergroup_view, methods=["POST"])
    app_obj.add_url_rule(
        "/api/user_group/<name>", view_func=usergroup_view, methods=["GET"]
    )
    # delete a user group
    app_obj.add_url_rule(
        "/api/user_group/<name>", view_func=usergroup_view, methods=["DELETE"]
    )

    usergroup_owned_view = usergroup.UserGroupOwnedService.as_view(
        "usergroup_owned_api"
    )
    # get all user groups owned by the requester
    app_obj.add_url_rule(
        "/api/user_group", view_func=usergroup_owned_view, methods=["GET"]
    )

    ugusers_view = ug_users.UserGroupUsersService.as_view("ugusers_api")
    # get a list of users in the user group
    # post add/change users in a usergroup
    app_obj.add_url_rule(
        "/api/user_group/<name>/users", view_func=ugusers_view, methods=["GET", "POST"]
    )

    permission_view = permission.PermissionService.as_view("permission_service")
    # get the permission of a permission-pair (user_group/sensor_group pair)
    # post sets the value of the permission-pair to an eligable value: r r/w r/w/p d/w
    app_obj.add_url_rule(
        "/api/permission",
        view_func=permission_view,
        methods=["GET", "POST", "DELETE", "PUT"],
    )

    permission_request_view = permission_request.PermissionRequestService.as_view(
        "permission_request_service"
    )
    # Push a notification to a mite owner that the user making this request wants permission to their mites
    app_obj.add_url_rule(
        "/api/permission/request",
        view_func=permission_request_view,
        methods=["GET", "POST"],
    )

    permission_uuid_request_view = permission_uuid.PermissionRequestUUIDService.as_view(
        "permission_request_uuid_service"
    )
    # Get or create UUIDs for permission request RabbitMQ queues
    app_obj.add_url_rule(
        "/api/permission/request/uuid",
        view_func=permission_uuid_request_view,
        methods=["GET"],
    )

    search_view = search.SearchService.as_view("search_service")
    # sensor search - search for sensors using the following keywords
    # 'Building', 'SourceName', 'SourceIdentifier', 'ID', 'Tags', 'MetaData'
    app_obj.add_url_rule("/api/sensor/search", view_func=search_view, methods=["POST"])

    users_view = user.UserService.as_view("users_api")
    # get returns info on the specified user
    # post changes/adds information to a specified user - if the user is new, an email will be sent
    # delete removes a user
    app_obj.add_url_rule("/api/user", view_func=users_view, methods=["POST"])
    app_obj.add_url_rule(
        "/api/user/<email>", view_func=users_view, methods=["GET", "DELETE"]
    )

    notifications_view = notification.NotificationClientIdService.as_view(
        "notification_client_id_service"
    )
    # Create, get or modify an ID used in the notification system
    app_obj.add_url_rule(
        "/api/notification/id", view_func=notifications_view, methods=["POST", "PUT"]
    )
