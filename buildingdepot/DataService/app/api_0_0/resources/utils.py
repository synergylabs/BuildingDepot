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
from ...models.ds_models import Sensor
from ...oauth_bd.views import Token
from ..errors import *
from ... import r
from flask import request
import sys
sys.path.append('/srv/buildingdepot')


permissions_val = {"u/d":1,"r/w":2,"r":3,"d/r":4}

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

def authenticate_acl(read_write):
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
                return jsonify({'response':'You are not authenticated to use to this sensor'})
            elif response  == read_write or response == 'r/w':
                return f(*args,**kwargs)
    	    elif response in ['undefined','r']:
                return jsonify({'response':'You are not authenticated to write to this sensor'})
    	    elif response == 'unauthorized':
                return jsonify({'response':'Access token not valid for this id'})
    	    else:
                return jsonify({'response':'Permission not defined or sensor does not exist'})
        return decorated_function
    return authenticate_write

def permission(sensor_name):

    headers = request.headers
    token = headers['Authorization'].split()[1]
    email = Token.objects(access_token=token).first().email

    sensor = Sensor.objects(name=sensor_name).first()
    if sensor == None:
        return 'invalid'

    #if admin then give complete access
    if email in get_admins():
        return 'r/w'

    current_res = 'u/d'
    usergroups = r.smembers('user:{}'.format(email))
    sensorgroups = r.smembers('sensor:{}'.format(sensor_name))
    previous,current = 0,0
    #Iterate over all the usergroups within which the user is present and the
    #sensorgroups within which the sensor is present and see if they have any
    #permission defined between them
    for usergroup in usergroups:
        for sensorgroup in sensorgroups:
            #Multiple permissions may exists for the same user and sensor relation.
            #This one chooses the most restrictive one by counting the number of tags
            current = int(r.get('tag-count:{}'.format(sensorgroup)))
            res = r.get('permission:{}:{}'.format(usergroup, sensorgroup))
            if current>previous and current!=0:
                previous = current
                if res!=None:
                    current_res = res
            elif current == previous:
                res = r.get('permission:{}:{}'.format(usergroup, sensorgroup))
                if res!=None:
                    print "permission is "+res
                    if permissions_val[res]>permissions_val[current_res]:
                        current_res = res
    return current_res
