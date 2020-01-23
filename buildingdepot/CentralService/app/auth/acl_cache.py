from .. import r
from ..models.cs_models import *

def invalidate_permission(sensorgroup):
    """ Takes the name of a sensor group and invalidates all the sensors
        in redis that belong to this sensor group"""
    sg_tags = SensorGroup.objects(name=sensorgroup).first()['tags']
    collection = Sensor._get_collection().find(form_query(sg_tags))
    try:
        pipe = r.pipeline()
        for sensor in collection:
            pipe.delete(sensor.get('name'))
        pipe.execute()
    except Exception as e:
        print (e)

def invalidate_user(usergroup,email):
    """Takes the id of the user that made the request and invalidates
       all the entries for this user (in redis) in every sensor in the
       sensor_group"""
    pipe = r.pipeline()
    permissions = Permission.objects(user_group=usergroup)
    for permission in permissions:
        sg_tags = SensorGroup.objects(name=permission['sensor_group']).first()['tags']
        collection = Sensor._get_collection().find(form_query(sg_tags))
        for sensor in collection:
            pipe.hdel(sensor.get('name',email))
        pipe.execute()

def form_query(values):
    res = []
    args = {}
    for tag in values:
        current_tag = {"tags.name": tag['name'], "tags.value": tag['value']}
        res.append(current_tag)
    args["$and"] = res
    return args





