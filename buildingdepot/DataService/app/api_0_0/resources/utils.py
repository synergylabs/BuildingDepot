from ...service.utils import validate_users, get_permission, get_admins
from ...models.ds_models import Sensor
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

def authenticate_acl(read_write):
    def authenticate_write(f):
        def decorated_function(*args, **kwargs):
    	    print args
	    print kwargs
	    email = kwargs['email']
    	    sensor_name = kwargs['name']
    	    response = permission(email,sensor_name)
    	    print "Response is "+response 
	    if response == 'd/r':
		return jsonify({'response':'You are not authenticated to use' \
                                    ' to this sensor'})
            elif response  == read_write or response == 'r/w':
    		  return f(*args,**kwargs)
    	    elif response in ['undefined','r']:
    		  return jsonify({'response':'You are not authenticated to write' \
    				    ' to this sensor'})
    	    elif response == 'unauthorized':
    		  return jsonify({'response':'Access token not valid for this id'})
    	    else:
    		  return jsonify({'response':'Sensor does not exist'})
        return decorated_function
    return authenticate_write

def permission(email, sensor_name):
    
    '''headers = request.headers
    token = headers['Authorization'].split()[1]
    email_db = Token.objects(access_token=token).first().email
    
    if email!=email_db:
	return 'unauthorized' '''
    
    sensor = Sensor.objects(name=sensor_name).first()
    if sensor == None:
        return 'invalid'
 
    if email in get_admins():
        return 'r/w'

    current_res = 'u/d'
    usergroups = r.smembers('user:{}'.format(email))
    sensorgroups = r.smembers('sensor:{}'.format(sensor_name))
    previous,current = 0,0
    for usergroup in usergroups:
        for sensorgroup in sensorgroups:
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
