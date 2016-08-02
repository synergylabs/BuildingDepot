import sys
from .. import r
from ..models.cs_models import *
from ..api_0_0.errors import *
from ..rest_api.helper import get_admins, check_if_super, get_ds
from ..rest_api import responses
from ..oauth_bd.views import Token
from flask import request

permissions_val = {"u/d": 1, "r/w/p": 2, "r/w": 3, "r": 4, "d/r": 5}


def super_required(f):
    def decorated_function(*args, **kwargs):
        email = get_email()
        user = User.objects(email=email).first()
        if user.role != 'super':
            return jsonify(responses.super_user_required)
        return f(*args, **kwargs)

    return decorated_function


def authenticate_acl(permission_required):
    """This is the function that defines the acl's and what level of access
       the user has to the specified sensor"""

    def authenticate_write(f):
        def decorated_function(*args, **kwargs):
            try:
                sensor_name = kwargs['name']
            except KeyError:
                sensor_name = request.get_json()['sensor_id']
            # Check what level of access this user has to the sensor
            response = permission(sensor_name)
            if response == 'u/d':
                if Sensor.objects(name=sensor_name).first() is None:
                    return jsonify({'success': 'False',
                                    'error': 'Sensor does not exist'})
                else:
                    return jsonify({'success': 'False', 'error': 'Permission not defined'})
            elif permissions_val[response] <= permissions_val[permission_required]:
                return f(*args, **kwargs)
            else:
                return jsonify({'success': 'False',
                                'error': 'You are not authenticated for this operation on the sensor'})

        return decorated_function

    return authenticate_write


def permission(sensor_name, email=None):
    if email is None: email = get_email()

    # Check if permission already cached
    current_res = r.hget(sensor_name, email)
    if current_res is not None:
        return current_res

    sensor = Sensor.objects(name=sensor_name).first()
    if sensor is None:
        return 'invalid'

    # check if super user
    if check_if_super(email) or email in get_admins(get_ds(sensor_name)):
        return 'r/w/p'

    # if admin of the sensor's dataservice or owner of sensor then give complete access
    if r.get('owner:{}'.format(sensor_name)) == email:
        r.hset(sensor_name, email, 'r/w/p')
        return 'r/w/p'

    current_res = check_db(sensor_name, email)
    # cache the latest permission
    r.hset(sensor_name, email, current_res)
    return current_res


def check_db(sensor, email):
    sensor_obj = Sensor.objects(name=sensor).first()
    if sensor_obj.owner == email:
        return 'r/w/p'

    tag_list = []
    # Retrieve sensor tags and form search query for Sensor groups
    for tag in sensor_obj['tags']:
        current_tag = {"name": tag['name'], "value": tag['value']}
        tag_list.append(current_tag)

    args = {}
    args["tags__exact"] = tag_list
    sensorgroups = SensorGroup.objects(**args)
    args = {}
    args["users__user_id"] = email
    usergroups = UserGroup.objects(**args)
    current_res = 'u/d'
    # Iterate over all sensor and user group combinations and find
    # resultant permission
    for usergroup in usergroups:
        for sensorgroup in sensorgroups:
            # Multiple permissions may exists for the same user and sensor relation.
            # This one chooses the most restrictive one by counting the number of tags
            res = r.hget('permission:{}:{}'.format(usergroup['name'], sensorgroup['name']), "permission")
            if res is None:
                permission_val = Permission.objects(sensor_group=sensorgroup['name'],
                                                    user_group=usergroup['name'])
                if permission_val:
                    res = permission_val.first()['permission']
            owner_email = r.hget('permission:{}:{}'.format(usergroup['name'], sensorgroup['name']), "owner")
            if res is not None and permission(sensor, owner_email) == 'r/w/p':
                if permissions_val[res] > permissions_val[current_res]:
                    current_res = res
    return current_res


def authorize_user(user_group, sensorgroup_name, email=None):
    if email is None: email = get_email()
    sensor_group = SensorGroup.objects(name=sensorgroup_name).first()
    tag_list = []
    for tag in sensor_group['tags']:
        current_tag = {"name": tag['name'], "value": tag['value']}
        tag_list.append(current_tag)
    args = {}
    args['building'] = sensor_group['building']
    args['tags__all'] = tag_list
    sensors = Sensor.objects(**args)
    for sensor in sensors:
        print sensor['name']
        if permission(sensor['name'], email) != 'r/w/p':
            return False
    return True


def authorize_addition(usergroup_name, email):
    user_group = UserGroup.objects(name=usergroup_name).first()
    if user_group['owner'] == email:
        return True

    for user in user_group.users:
        print type(user['manager'])
        if user['user_id'] == email and user['manager']:
            return True
    return False


def get_email():
    headers = request.headers
    token = headers['Authorization'].split()[1]
    return Token.objects(access_token=token).first().email
