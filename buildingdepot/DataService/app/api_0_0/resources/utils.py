"""
DataService.api_0_0.resources.utils
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains the definitions for all the various decorator functions that are
called to authenticate,validate email,define what level of access the user
has to the specified sensor.

@copyright: (c) 2020 SynergyLabs
@license: CMU License. See License file for details.
"""

import sys
from flask import request

from ..errors import *
from ... import r
from ...models.ds_models import Sensor, SensorGroup, UserGroup, Permission
from ...oauth_bd.views import Token
from ...rest_api.helper import check_if_super
from ...service.utils import validate_users, get_permission, get_admins

sys.path.append("/srv/buildingdepot")

permissions_val = {"u/d": 1, "r/w/p": 2, "r/w": 3, "r": 4, "d/r": 5}


def success():
    response = jsonify({"success": "True"})
    response.status_code = 200
    return response


def validate_email(f):
    """Checks if user exists in the system"""

    def decorated_function(*args, **kwargs):
        email = [kwargs["email"]]
        if not validate_users(email):
            return not_exist("User {} does not exist".format(email))
        return f(*args, **kwargs)

    return decorated_function


def validate_sensor(f):
    """Validates the uuid of the given sensor to see if it exists"""

    def decorated_function(*args, **kwargs):
        sensor_name = kwargs["sensor_name"]
        if Sensor.objects(name=sensor_name).first() is None:
            return not_exist("Sensor {} does not exist".format(sensor_name))
        return f(*args, **kwargs)

    return decorated_function


def authenticate_acl(permission_required):
    """This is the function that defines the acl's and what level of access
    the user has to the specified sensor"""

    def authenticate_write(f):
        def decorated_function(*args, **kwargs):
            try:
                sensor_name = kwargs["name"]
            except KeyError:
                sensor_name = request.get_json()["sensor_id"]
            # Check what level of access this user has to the sensor
            response = permission(sensor_name)
            if response == "u/d":
                if Sensor.objects(name=sensor_name).first() is None:
                    return jsonify(
                        {"success": "False", "error": "Sensor does not exist"}
                    )
                else:
                    return jsonify(
                        {"success": "False", "error": "Permission not defined"}
                    )
            elif permissions_val[response] <= permissions_val[permission_required]:
                return f(*args, **kwargs)
            else:
                return jsonify(
                    {
                        "success": "False",
                        "error": "You are not authenticated for this operation on the sensor",
                    }
                )

        return decorated_function

    return authenticate_write


def permission(sensor_name, email=None):
    if email is None:
        email = get_email()
    # Check if permission already cached
    current_res = r.hget(sensor_name, email)
    if current_res is not None:
        return current_res

    sensor = Sensor.objects(name=sensor_name).first()
    if sensor is None:
        return "u/d"

    # if admin or owner then give complete access or email in get_admins()
    if r.get("owner:{}".format(sensor_name)) == email or check_if_super(email):
        r.hset(sensor_name, email, "r/w/p")
        return "r/w/p"

    print("Not owner or admin")

    current_res = "u/d"
    usergroups = r.smembers("user:{}".format(email))
    sensorgroups = r.smembers("sensor:{}".format(sensor_name))
    previous, current = 0, 0
    # Iterate over all the usergroups within which the user is present and the
    # sensorgroups within which the sensor is present and find permissions
    for usergroup in usergroups:
        for sensorgroup in sensorgroups:
            # Multiple permissions may exists for the same user and sensor relation.
            # This one chooses the most restrictive one by counting the number of tags
            res = r.hget(
                "permission:{}:{}".format(usergroup, sensorgroup), "permission"
            )
            owner_email = r.hget(
                "permission:{}:{}".format(usergroup, sensorgroup), "owner"
            )
            print(res)
            if res is not None and permission(sensor_name, owner_email) == "r/w/p":
                if permissions_val[res] > permissions_val[current_res]:
                    current_res = res
    # If permission couldn't be calculated from cache go to MongoDB
    if current_res == "u/d":
        current_res = check_db(sensor_name, email)
    # cache the latest permission
    r.hset(sensor_name, email, current_res)
    return current_res


def batch_permission_check(sensors_list, email=None):
    permissions = {}  # dict to store permissions
    missing_from_cache = []  # permission not found in cache
    sensors_missing = []  # sensors not foun
    sensors_missing_from_cache = []  # sensor info not found in cache (owner:sensor)
    not_owner_sensors = []  # sensors which the user does not own

    if not email:
        email = get_email()

    # Get cached permissions for sensor
    p = r.pipeline()
    for sensor in sensors_list:
        p.hget(sensor, email)
    cache_results = p.execute()

    # If found in cache, add to permissions dict. If not, append to missing_from_cache
    for i in range(len(sensors_list)):
        if cache_results[i]:
            permissions[sensors_list[i]] = cache_results[i]
        else:
            missing_from_cache.append(sensors_list[i])

    if not missing_from_cache:
        return permissions

    # check if the owner:sensor key is present => sensor exists
    redis_sensor_keys = ["".join(["owner:", sensor]) for sensor in sensors_list]
    owners = dict(list(zip(redis_sensor_keys, r.mget(*redis_sensor_keys))))
    for k, v in list(owners.items()):
        if not v:
            sensors_missing_from_cache.append(k[6:])

    # for sensors not found, query MongoDB
    if sensors_missing_from_cache:
        sensors = Sensor._get_collection().find(
            {"name": {"$in": sensors_missing_from_cache}}
        )
        for sensor in sensors:
            owners["".join(["owner:", sensor.name])] = sensor.owner

    # Invalid sensors
    for k, v in list(owners.items()):
        if not v:
            del owners[k]
            permissions[k[6:]] = "absent"
            sensors_missing.append(k[6:])

    # If the user is sensor owner or admin, give complete access and add to cache
    p = r.pipeline()
    for k, v in list(owners.items()):
        if check_if_super(email) or email == v:
            permissions[k[6:]] = "r/w/p"
            r.hset(k[6:], email, "r/w/p")
        else:
            not_owner_sensors.append(k[6:])
    p.execute()
    if not not_owner_sensors:
        return permissions

    # Calculating most restrictive sensor:user permissions from usergroup:sensorgroup permissions
    usergroups = r.smembers("".join(["user:", email]))
    for sensor in not_owner_sensors:
        current_res = "u/d"
        sensorgroups = r.smembers("".join(["sensor:", sensor]))
        for usergroup in usergroups:
            for sensorgroup in sensorgroups:
                res = r.hget(
                    "permission:{}:{}".format(usergroup, sensorgroup), "permission"
                )
                owner_email = r.hget(
                    "permission:{}:{}".format(usergroup, sensorgroup), "owner"
                )
                if res and permission(sensor, owner_email) == "r/w/p":
                    if permissions_val[res] > permissions_val[current_res]:
                        current_res = res

            # If not found, check from MongoDB
            if current_res == "u/d":
                mongo_permission = check_db(sensor, email)
                permissions[sensors_list[i]] = mongo_permission
                r.hset(sensor, email, mongo_permission)
            else:
                permissions[sensor] = current_res
                r.hset(sensor, email, current_res)
    return permissions


def check_db(sensor, email):
    sensor_obj = Sensor.objects(name=sensor).first()
    args = {}
    tag_list = []
    # Retrieve sensor tags and form search query for Sensor groups
    for tag in sensor_obj["tags"]:
        current_tag = {"name": tag["name"], "value": tag["value"]}
        tag_list.append(current_tag)
    args["tags__size"] = len(tag_list)
    args["tags__all"] = tag_list
    sensor_groups = SensorGroup.objects(**args)
    args = {}
    args["users__user_id"] = email
    user_groups = UserGroup.objects(**args)
    current_res = "u/d"
    # Iterate over all sensor and user group combinations and find
    # resultant permission
    for sensor_group in sensor_groups:
        for user_group in user_groups:
            permission = Permission.objects(
                sensor_group=sensor_group["name"], user_group=user_group["name"]
            )
            if permission.first() is not None:
                curr_permission = permission.first()["permission"]
                if permissions_val[curr_permission] > permissions_val[current_res]:
                    current_res = curr_permission
    return current_res


def authorize_user(user_group, sensorgroup_name, email=None):
    if email is None:
        email = get_email()
    sensor_group = SensorGroup.objects(name=sensorgroup_name).first()
    tag_list = []
    for tag in sensor_group["tags"]:
        current_tag = {"name": tag["name"], "value": tag["value"]}
        tag_list.append(current_tag)
    args = {}
    args["building"] = sensor_group["building"]
    args["tags__all"] = tag_list
    sensors = Sensor.objects(**args)
    for sensor in sensors:
        print((sensor["name"]))
        if permission(sensor["name"], email) != "r/w/p":
            return False
    return True


def authorize_addition(usergroup_name, email):
    user_group = UserGroup.objects(name=usergroup_name).first()
    if user_group["owner"] == email:
        return True

    for user in user_group.users:
        print((type(user["manager"])))
        if user["user_id"] == email and user["manager"]:
            return True
    return False


def get_email():
    headers = request.headers
    token = headers["Authorization"][7:]
    user = r.get("".join(["oauth:", token]))
    if user:
        return user
    token = Token.objects(access_token=token).first()
    return token.email
