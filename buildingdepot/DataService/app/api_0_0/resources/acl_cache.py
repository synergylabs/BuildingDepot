from ... import r
from ...models.ds_models import *

def invalidate_permission(sensorgroup):
    """ Takes the name of a sensor group and invalidates all the sensors
        in redis that belong to this sensor group"""
    sensor_group = SensorGroup.objects(name=sensorgroup).first()
    pipe = r.pipeline()
    sensors_list = r.smembers('sensorgroup:{}'.format(sensor_group['name']))
    for sensor in sensors_list:
        pipe.delete(sensor)
    pipe.execute()

def invalidate_user(usergroup,email):
    """Takes the id of the user that made the request and invalidates
       all the entries for this user (in redis) in every sensor in the
       sensor_group"""
    pipe = r.pipeline()
    permissions = Permission.objects(user_group=usergroup)
    for permission in permissions:
        sensors_list = r.smembers('sensorgroup:{}'.format(permission['sensor_group']))
        for sensor in sensors_list:
            pipe.hdel(sensor,email)
    pipe.execute()






