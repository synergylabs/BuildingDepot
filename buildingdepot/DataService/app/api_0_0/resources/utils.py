from ...service.utils import validate_users, get_permission, get_admins
from ...models.ds_models import Sensor
from ..errors import *
from ... import r


def success():
    response = jsonify({'success': 'True'})
    response.status_code = 200
    return response


def validate_email(f):
    def decorated_function(*args, **kwargs):
        email = [kwargs['email']]
        if not validate_users(email):
            return not_exist('User {} does not exist'.format(email))
        return f(*args, **kwargs)
    return decorated_function


def validate_sensor(f):
    def decorated_function(*args, **kwargs):
        sensor_name = kwargs['sensor_name']
        if Sensor.objects(name=sensor_name).first() is None:
            return not_exist('Sensor {} does not exist'.format(sensor_name))
        return f(*args, **kwargs)
    return decorated_function


def permission(email, sensor_name):
    if email in get_admins():
        return 'r/w'

    res = None
    usergroups = r.smembers('user:{}'.format(email))
    sensorgroups = r.smembers('sensor:{}'.format(sensor_name))

    for usergroup in usergroups:
        for sensorgroup in sensorgroups:
            res = r.get('permission:{}:{}'.format(usergroup, sensorgroup))
            if res == 'r/w':
                return 'r/w'
    if res == 'r':
        return 'r'

    sensor = Sensor.objects(name=sensor_name).first()
    sensor_tags = ['{}:{}'.format(tag.name, tag.value) for tag in sensor.tags]
    return get_permission(sensor_tags, sensor.building, email)


