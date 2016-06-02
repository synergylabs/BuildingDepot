"""
DataService.api_0_0.resources.utils
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains the definitions for all the various decorator functions that are
called to authenticate,validate email,define what level of access the user
has to the specified sensor.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from ...service.utils import validate_users, get_permission, get_admins
from ...models.ds_models import Sensor,SensorGroup,UserGroup,Permission
from ...oauth_bd.views import Token
from ..errors import *
from ... import r
from flask import request
import sys
sys.path.append('/srv/buildingdepot')


permissions_val = {"u/d":1,"r/w/p":2,"r/w":3,"r":4,"d/r":5}

def success():
    response = jsonify({'success': 'True'})
    response.status_code = 200
    return response


def validate_email(f):
    """Checks if user exists in the system"""
    def decorated_function(*args, **kwargs):
        email = [kwargs['email']]
        if not validate_users(email):
            return not_exist('User {} does not exist'.format(email))
        return f(*args, **kwargs)
    return decorated_function


def validate_sensor(f):
    """Validates the uuid of the given sensor to see if it exists"""
    def decorated_function(*args, **kwargs):
        sensor_name = kwargs['sensor_name']
        if Sensor.objects(name=sensor_name).first() is None:
            return not_exist('Sensor {} does not exist'.format(sensor_name))
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
            #Check what level of access this user has to the sensor
            response = permission(sensor_name)
            if response == 'd/r':
                return jsonify({'success':'False',
                    'error':'You are not authenticated to use this sensor'})
            elif response  == permission_required or response == 'r/w/p':
                return f(*args,**kwargs)
    	    elif response in ['r','r/w']:
                return jsonify({'success':'False',
                    'error':'You are not authenticated for this operation on the sensor'})
    	    else:
                if Sensor.objects(name=sensor_name).first() is None:
                    return jsonify({'success':'False',
                        'error':'Sensor does not exist'})
                else:
                    return jsonify({'success':'False','error':'Permission not defined'})
        return decorated_function
    return authenticate_write

def permission(sensor_name,email=None):

    if email is None : email = get_email()

    #Check if permission already cached
    current_res = r.hget(sensor_name,email)
    if current_res is not None:
        return current_res

    sensor = Sensor.objects(name=sensor_name).first()
    if sensor is None:
        return 'invalid'

    #if admin or owner then give complete access
    if r.get('owner:{}'.format(sensor_name)) == email or email in get_admins():
        r.hset(sensor_name,email,'r/w/p')
        return 'r/w/p'

    print "Not owner or admin"

    current_res = 'u/d'
    usergroups = r.smembers('user:{}'.format(email))
    sensorgroups = r.smembers('sensor:{}'.format(sensor_name))
    previous,current = 0,0
    #Iterate over all the usergroups within which the user is present and the
    #sensorgroups within which the sensor is present and find permissions
    for usergroup in usergroups:
        for sensorgroup in sensorgroups:
            #Multiple permissions may exists for the same user and sensor relation.
            #This one chooses the most restrictive one by counting the number of tags
            res = r.hget('permission:{}:{}'.format(usergroup, sensorgroup),"permission")
            owner_email = r.hget('permission:{}:{}'.format(usergroup, sensorgroup),"owner")
            print res
            if res is not None and permission(sensor_name,owner_email)=='r/w/p':
                if permissions_val[res]>permissions_val[current_res]:
                    current_res = res
    #If permission couldn't be calculated from cache go to MongoDB
    if current_res=='u/d':
        current_res = check_db(sensor_name,email)
    #cache the latest permission
    r.hset(sensor_name,email,current_res)
    return current_res

def check_db(sensor,email):
    sensor_obj = Sensor.objects(name=sensor).first()
    args={}
    tag_list = []
    #Retrieve sensor tags and form search query for Sensor groups
    for tag in sensor_obj['tags']:
        current_tag = {"name":tag['name'],"value":tag['value']}
        tag_list.append(current_tag)
    args['tags__all'] = tag_list
    sensor_groups = SensorGroup.objects(**args)
    args={}
    args['users__all'] = [email]
    user_groups = UserGroup.objects(**args)
    current_res = 'u/d'
    #Iterate over all sensor and user group combinations and find
    #resultant permission
    for sensor_group in sensor_groups:
        for user_group in user_groups:
            permission = Permission.objects(sensor_group=sensor_group['name'],
                user_group=user_group['name'])
            if permission.first() is not None:
                curr_permission = permission.first()['permission']
                print "curr_permission is "+curr_permission+"Sensor group is "+sensor_group['name']+" User group is "+user_group['name']
                if permissions_val[curr_permission] > permissions_val[current_res]:
                    current_res = curr_permission
    return current_res

def authorize_user(user_group,sensorgroup_name,email=None):
    if email is None : email = get_email()
    sensor_group = SensorGroup.objects(name=sensorgroup_name).first()
    tag_list = []
    for tag in sensor_group['tags']:
        current_tag = {"name":tag['name'],"value":tag['value']}
        tag_list.append(current_tag)
    args={}
    args['building'] = sensor_group['building']
    args['tags__all'] = tag_list
    sensors  = Sensor.objects(**args)
    for sensor in sensors:
        print sensor['name']
        if permission(sensor['name'],email) != 'r/w/p':
            return False
    return True

def authorize_addition(usergroup_name,email):
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

