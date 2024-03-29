"""
CentralReplica.main
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains the definitions for all the RPC's that the DataService
calls in order to avoid talking to the CentralService all the time.

@copyright: (c) 2024 SynergyLabs
@license: CMU License. See License file for details.
"""

import redis
from config import Config
from models import *
from mongoengine import connect
from socketserver import ThreadingMixIn
from xmlrpc.server import SimpleXMLRPCServer

connect(
    db=Config.MONGODB_DATABASE,
    host=Config.MONGODB_HOST,
    port=Config.MONGODB_PORT,
    username=Config.MONGODB_USERNAME,
    password=Config.MONGODB_PWD,
    authentication_source="admin",
)

r = redis.Redis(
    host=Config.REDIS_HOST, password=Config.REDIS_PWD, decode_responses=True
)


class ThreadXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass


def get_user(email, password):
    user = User.objects(email=email).first()
    if user is not None and user.verify_password(password):
        return True
    return False


def create_sensor(sensor_id, email, fields=None, parent=None):
    r.set("owner:{}".format(sensor_id), email)
    if parent:
        r.set("owner:{}".format(sensor_id), email)
        r.sadd("views:{}".format(parent), sensor_id)
        r.set("fields:{}".format(sensor_id), fields)
        r.set("parent:{}".format(sensor_id), parent)
        fields = [field.strip() for field in fields.split(",")]
        for field in fields:
            r.sadd("{}:{}".format(parent, field), sensor_id)
        r.sadd("views", sensor_id)


def invalidate_sensor(sensor_id):
    r.delete("sensor:{}".format(sensor_id))


def delete_sensor(sensor_id, parent=None):
    r.delete("sensor:{}".format(sensor_id))
    r.delete("owner:{}".format(sensor_id))
    if parent:
        fields = r.get("fields:{}".format(sensor_id))
        if fields:
            fields = fields.split(",")
            fields = [field.strip() for field in fields]
            for field in fields:
                r.srem("{}:{}".format(parent, field), sensor_id)
        r.delete("fields:{}".format(sensor_id))
        r.delete("parent:{}".format(sensor_id))
        r.delete(sensor_id)
        r.srem("views", sensor_id)
        # cache process done
        Sensor.objects(name=sensor_id).delete()


def create_permission(user_group, sensor_group, email, permission):
    invalidate_permission(sensor_group)
    r.hset(
        "permission:{}:{}".format(user_group, sensor_group), "permission", permission
    )
    r.hset("permission:{}:{}".format(user_group, sensor_group), "owner", email)


def delete_permission(user_group, sensor_group):
    invalidate_permission(sensor_group)
    r.delete("permission:{}:{}".format(user_group, sensor_group))


def invalidate_permission(sensorgroup):
    """Takes the name of a sensor group and invalidates all the sensors
    in redis that belong to this sensor group"""
    sg_tags = SensorGroup.objects(name=sensorgroup).first()["tags"]
    if len(sg_tags) == 0:
        return
    collection = Sensor._get_collection().find(form_query(sg_tags))
    pipe = r.pipeline()
    for sensor in collection:
        pipe.delete(sensor.get("name"))
    pipe.execute()


def invalidate_user(usergroup, email):
    """Takes the id of the user that made the request and invalidates
    all the entries for this user (in redis) in every sensor in the
    sensor_group"""
    pipe = r.pipeline()
    permissions = Permission.objects(user_group=usergroup)
    for permission in permissions:
        sg_tags = SensorGroup.objects(name=permission["sensor_group"]).first()["tags"]
        collection = Sensor._get_collection().find(form_query(sg_tags))
        for sensor in collection:
            pipe.hdel(sensor.get("name"), email)
        pipe.execute()


def form_query(values):
    res = []
    args = {}
    for tag in values:
        current_tag = {"tags.name": tag["name"], "tags.value": tag["value"]}
        res.append(current_tag)
    args["$and"] = res
    return args


def get_admins(name):
    """Get the list of admins in the DataService"""
    obj = DataService.objects(name=name).first()
    if obj is None:
        return []
    return list(obj.admins)


# Create a local RPC server and register the functions
svr = ThreadXMLRPCServer(("", 8080), allow_none=True)
svr.register_function(get_user)
svr.register_function(create_sensor)
svr.register_function(invalidate_sensor)
svr.register_function(delete_sensor)
svr.register_function(create_permission)
svr.register_function(delete_permission)
svr.register_function(invalidate_permission)
svr.register_function(invalidate_user)
svr.register_function(get_admins)
svr.serve_forever()
