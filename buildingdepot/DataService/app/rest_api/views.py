"""
DataService.rest_api.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains all the definitions for the REST api's that are exposed to the user.
All requests will need to be authenticated using an OAuth token and sensor specific
requests will also have an additional check where the ACL's are referenced to see if
the user has access to the specific sensor

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask import json,render_template,abort
from flask import request, redirect, url_for, jsonify, flash
from . import api
from ..models.ds_models import *
from ..service.utils import *
from uuid import uuid4
from .. import r, influx,oauth,pubsub,exchange
from werkzeug.security import gen_salt
import sys,time,influxdb,urllib
sys.path.append('/srv/buildingdepot')
from utils import get_user_oauth
from ..api_0_0.resources.utils import *


permissions = {"rw":"r/w","r":"r","dr":"d/r"}


@api.route('/sensor/<name>', methods=['GET'])
@api.route('/sensor', methods=['POST'])
@oauth.require_oauth()
def sensor_create(name=None):
    """Check if the building the user has specified is valid and if so create
     the sensor and return the uuid"""
    if request.method == 'POST':
        building = request.args.get('building')
        if building is None:
            return jsonify({'success': 'False','error':'Missing parameters'})

        for item in get_building_choices(current_app.config['NAME']):
            if building in item:
                uuid = str(uuid4())
                Sensor(name=uuid,
                           source_name=xstr(request.args.get('name')),
                           source_identifier=xstr(request.args.get('identifier')),
                           building=building).save()
                return jsonify({'success': 'True','uuid':uuid})
        return jsonify({'success': 'False','error':'Building does not exist'})
    elif request.method == 'GET':
        if name is None:
            return jsonify({'success': 'False','error':'Missing parameters'})
        sensor = Sensor.objects(name=name).first()
        if sensor is None:
            return jsonify({'success': 'False','error':'Sensor doesn\'t exist'})
        tags_owned = [{'name': tag.name, 'value': tag.value} for tag in sensor.tags]
        metadata = Sensor._get_collection().find({'name': name}, {'metadata': 1, '_id': 0})[0]['metadata']
        metadata = [{'name': key, 'value': val} for key, val in metadata.iteritems()]
        return jsonify ({'building': str(sensor.building),
            'name' : str(sensor.name),
            'tags' : tags_owned,
            'metadata' : metadata,
            'source_identifier' : str(sensor.source_identifier),
            'source_name' : str(sensor.source_name)
        })


@api.route('/sensor/<name>/timeseries', methods=['GET'])
@oauth.require_oauth()
@authenticate_acl('r')
def get_data(name):
    """Reads the time series data of the sensor over the interval specified and returns it to the
       user. If resolution is also specified then data points will be averaged over the resolution
       period and returned"""

    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    resolution = request.args.get('resolution')

    if not all([start_time,end_time]):
        return jsonify({'error':'Missing parameters'})

    if resolution!=None:
        try:
            data = influx.query('select mean(value) from "' + name + '" where (time>\''+ timestamp_to_time_string(float(start_time))\
             +'\' and time<\'' + timestamp_to_time_string(float(end_time)) +'\')'+" GROUP BY time("+resolution+")")
        except influxdb.exceptions.InfluxDBClientError:
            return jsonify({'error':'Too many points for this resolution'})
    else:
        data = influx.query('select * from "' + name + '" where time>\''+ timestamp_to_time_string(float(start_time))\
         +'\' and time<\'' + timestamp_to_time_string(float(end_time)) +'\'')
    return jsonify({'data':data.raw,'response':'success'})

def timestamp_to_time_string(t):
    '''Converts a unix timestamp to a string representation of the timestamp
    Args:
        t: A unix timestamp float
    Returns
        A string representation of the timestamp
    '''
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t)) + str(t-int(t))[1:10]+ 'Z'

@api.route('/sensor/list', methods=['GET'])
@oauth.require_oauth()
def get_sensors_metadata():
    """ If request type is params all the sensors with the specified paramter key and values are returned,
        for request type of tags all the sensors with the matching tag key and value are searched for and
        returned, similarly for metadata"""
    request_type = request.args.get('filter')

    if (request_type is None) or (len(request.args)<2):
        return jsonify({'success':'False','error':'Missing parameters'})

    for key, val in request.args.iteritems():
        if key!='filter':
            param = urllib.unquote(key).decode('utf8')
            value = urllib.unquote(val).decode('utf8')
            print param,value

    if request_type == "params":
        list_sensors = Sensor._get_collection().find({param:value})
        return jsonify({'data': create_response(list_sensors)})
    elif request_type == "tags":
        list_sensors = Sensor._get_collection().find({request_type:{'name':param, 'value': value}})
        return jsonify({'data': create_response(list_sensors)})
    elif request_type == "metadata":
        list_sensors = Sensor._get_collection().find({request_type+"."+param:value})
        return jsonify({'data': create_response(list_sensors)})

def create_json(sensor):
    """Simple function that creates a json object to return for each sensor"""
    json_object = { 'building': sensor.get('building'),
            'name' : sensor.get('name'),
            'tags' : sensor.get('tags'),
            'metadata' : sensor.get('metadata'),
            'source_identifier' : sensor.get('source_identifier'),
            'source_name' : sensor.get('source_name')
            }
    return json_object

def create_response(sensors):
    """Iterates over the list and generates a json response of sensors list"""
    sensor_list = []
    for sensor in sensors:
        json_temp = create_json(sensor)
        sensor_list.append(json_temp)
    return sensor_list

@api.route('/sensor/<name>/metadata', methods=['GET', 'POST'])
def sensor_metadata(name):
    """For the specified sensor returns all the metadata attached to it in a json response"""
    if request.method == 'GET':
        metadata = Sensor._get_collection().find({'name': name}, {'metadata': 1, '_id': 0})[0]['metadata']
        metadata = [{'name': key, 'value': val} for key, val in metadata.iteritems()]
        return jsonify({'data': metadata})
    #For a POST request upadtes the metadata
    else:
        metadata = {pair['name']: pair['value'] for pair in request.get_json()['data'] if pair['name'] != ''}
        building = Sensor.objects(name=name).first()
        building.update(set__metadata=metadata)
        return jsonify({'success': 'True'})


@api.route('/sensor/<name>/subscribers', methods=['GET', 'POST'])
def sensor_subscribers(name):
    """ Either updates or retrieves the list of subscribers for the sensor with uuid
        <name> depending on whether the request is GET or POST"""
    if request.method == 'GET':
        subscribers = r.smembers('subscribers:{}'.format(name))
        data = [{'email': subscriber} for subscriber in subscribers]
        return jsonify({'subscribers': data})
    else:
        new_subscribers = [subscriber['email'] for subscriber in request.get_json()['data']]
        if validate_users(new_subscribers):
            old_subscribers = r.smembers('subscribers:{}'.format(name))
            #Finds the new users that have been added and the users that have
            #been deleted in order to update the cache
            added, deleted = get_add_delete(old_subscribers, new_subscribers)
            pipe = r.pipeline()
            sensor = Sensor.objects(name=name).first()
            for email in added:
                pipe.sadd('subscribed_sensors:{}'.format(email), name)
            for email in deleted:
                pipe.srem('subscribed_sensors:{}'.format(email), name)

            pipe.delete('subscribers:{}'.format(name))
            for subscriber in new_subscribers:
                pipe.sadd('subscribers:{}'.format(name), subscriber)
            pipe.execute()
            return jsonify({'success': 'True'})
        return jsonify({'success': 'False'})

@api.route('/sensor/timeseries', methods=['POST'])
@oauth.require_oauth()
def insert_timeseries_to_bd():
    '''
    Args as data:
        [
            {
                "sensor_uuid":
                "samples":[
                        {
                            "time": A unix timestamp of a sampling
                            "value": A sensor value
                        },
                        { more times and values }
                    ]
            },
            { more sensors }
        ]
    Returns:
        {
            "success": True or False
            "error": details of an error if it happends
        }
    '''

    try:
        json = request.get_json()
        points = []
        for sensor in json:
            # check a user has permission
            unauthorised_sensor = []
            if permission(sensor['sensor_uuid'])=='r/w':
                for sample in sensor['samples']:
                    dic = {
                        'measurement':sensor['sensor_uuid'],
                        'time':timestamp_to_time_string(sample['time']),
                        'fields':{
                            'inserted_at':timestamp_to_time_string(time.time()),
                            'value':sample['value']
                        }
                    }
                    points.append(dic)
            else:
                unauthorised_sensor.append(sensor['sensor_uuid'])
    except KeyError:
        abort(400)

    result = influx.write_points(points)

    dic = {}

    if result:
        dic['success'] = 'True'
        dic['unauthorised_sensor'] = unauthorised_sensor
    else:
        dic['success'] = 'False'
        dic['error'] = 'Error in writing in InfluxDB'

    return jsonString(dic)

def jsonString(obj,pretty=False):
    if pretty == True:
        return json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': ')) + '\n'
    else:
        return json.dumps(obj)

@api.route('/sensor/<name>/tags', methods=['GET', 'POST'])
def sensor_tags(name):
    """Returns/Updates the list of tags that are attached to the sensor with the uuid <name>"""
    if request.method == 'GET':
        #If request is a GET then return the list of tags
        obj = Sensor.objects(name=name).first()
        tags_owned = [{'name': tag.name, 'value': tag.value} for tag in obj.tags]
        tags = get_building_tags(obj.building)
        return jsonify({'tags': tags, 'tags_owned': tags_owned})
    else:
        #If request is a POST then update the tags
        tags = request.get_json()['data']

        # cache process
        sensor = Sensor.objects(name=name).first()
        building = sensor.building
        #Get old tags and new tags and find the list of tags that have to be added and deleted
        #based on the response from get_add_delete
        old = ['tag:{}:{}:{}'.format(building, tag.name, tag.value) for tag in sensor.tags]
        new = ['tag:{}:{}:{}'.format(building, tag['name'], tag['value']) for tag in tags]
        added, deleted = get_add_delete(old, new)
        pipe = r.pipeline()
        for tag in added:
            pipe.sadd(tag, name)
        for tag in deleted:
            pipe.srem(tag, name)
        pipe.execute()

        # cache process done, update the values in MongoDB
        Sensor.objects(name=name).update(set__tags=tags)

        added = [tag.replace('tag', 'tag-sensorgroup', 1) for tag in added]
        deleted = [tag.replace('tag', 'tag-sensorgroup', 1) for tag in deleted]

        pipe = r.pipeline()
        #Also update in the cache the sensorgroups and tags that this specific sensor is attached to
        for key in added:
             for sensorgroup_name in r.smembers(key):
                sensorgroup = SensorGroup.objects(name=sensorgroup_name).first()
                sensorgroup_tags = {'tag:{}:{}:{}'.format(building, tag.name, tag.value) for tag in sensorgroup.tags}
                if sensorgroup_tags.issubset(new):
                    pipe.sadd('sensorgroup:{}'.format(sensorgroup_name), sensor.name)
                    pipe.sadd('sensor:{}'.format(sensor.name), sensorgroup_name)

        for key in deleted:
            for sensorgroup_name in r.smembers(key):
                pipe.srem('sensorgroup:{}'.format(sensorgroup_name), sensor.name)
                pipe.srem('sensor:{}'.format(sensor.name), sensorgroup_name)

        pipe.execute()

        return jsonify({'success': 'True'})


@api.route('/sensor_group/<name>/tags', methods=['GET', 'POST'])
def sensorgroup_tags(name):
    """Returns/Updates the list of tags that are attached to the sensorgroup <name>"""
    if request.method == 'GET':
        #Retrieve the list
        obj = SensorGroup.objects(name=name).first()
        tags_owned = [{'name': tag.name, 'value': tag.value} for tag in obj.tags]
        tags = get_building_tags(obj.building)
        return jsonify({'tags': tags, 'tags_owned': tags_owned})
    else:
        tags = request.get_json()['data']
        #cache process
        sensorgroup = SensorGroup.objects(name=name).first()
        old = ['tag-sensorgroup:{}:{}:{}'.format(sensorgroup.building, tag.name, tag.value) for tag in sensorgroup.tags]
        new = ['tag-sensorgroup:{}:{}:{}'.format(sensorgroup.building, tag['name'], tag['value']) for tag in tags]
        added, deleted = get_add_delete(old, new)
        pipe = r.pipeline()
        for tag in added:
            pipe.sadd(tag, name)
        for tag in deleted:
            pipe.srem(tag, name)
        pipe.set('tag-count:{}'.format(name),len(new))
        # recalculate the sensors that this sensorgroup contains
        tags_owned = ['tag:{}:{}:{}'.format(sensorgroup.building, tag['name'], tag['value']) for tag in tags]

        old_sensors = r.smembers('sensorgroup:{}'.format(name))
        new_sensors = r.sinter(tags_owned) if len(tags_owned) > 0 else []
        added, deleted = get_add_delete(old_sensors, new_sensors)

        for sensor_name in added:
            pipe.sadd('sensor:{}'.format(sensor_name), name)
        for sensor_name in deleted:
            pipe.srem('sensor:{}'.format(sensor_name), name)

        r.delete('sensorgroup:{}'.format(name))
        for item in new_sensors:
            pipe.sadd('sensorgroup:{}'.format(name), item)
        pipe.execute()
        #cache process done
        SensorGroup.objects(name=name).update(set__tags=tags)
        return jsonify({'success': 'True'})


@api.route('/user_group', methods=['POST'])
def usergroup_create():
    #Create the usergroup
    name = request.args.get('name')
    description = request.args.get('description')
    if name is None:
        return jsonify({'success':'False','error':'Missing parameters'})
    UserGroup(name=xstr(name),
                description=xstr(description)).save()
    return jsonify({'success':'True'})

@api.route('/sensor_group', methods=['POST'])
def sensorgroup_create():
    #Create the sensorgroup
    name = request.args.get('name')
    building = request.args.get('building')
    description = request.args.get('description')

    if not all([name,building]):
        return jsonify({'success':'False','error':'Missing parameters'})

    #Get the list of buildings and verify that the one specified in the
    #request exists
    buildings_list = get_building_choices(current_app.config['NAME'])
    for item in buildings_list:
        if building in item:
            SensorGroup(name=xstr(name),building=xstr(building),
                description=xstr(description)).save()
            return jsonify({'success':'True'})

    return jsonify({'success':'False','error':'Building does not exist'})

@api.route('/user_group/<name>/users', methods=['GET', 'POST'])
def usergroup_users(name):
    """ Updates/Returns the lists of users that are attached to the usergroup <name>"""
    if request.method == 'GET':
        obj = UserGroup.objects(name=name).first()
        return jsonify({'users': obj.users})
    else:
        emails = request.get_json()['data']
        if validate_users(emails):
            # cache process
            user_group = UserGroup.objects(name=name).first()
            #Recalculate the list of users that have to be added and
            #removed from this group based on the new list received
            added, deleted = get_add_delete(user_group.users, emails)
            pipe = r.pipeline()
            for user in added:
                pipe.sadd('user:{}'.format(user), user_group.name)
            for user in deleted:
                pipe.srem('user:{}'.format(user), user_group.name)
            pipe.execute()
            # cache process done
            UserGroup.objects(name=name).update(set__users=emails)
            return jsonify({'success': 'True'})
        return jsonify({'success': 'False','error':'One or more users not registered'})

@api.route('/apps',methods=['GET','POST'])
def register_app():
    json_data = request.get_json()
    try:
        email = json_data['email']
    except Exception as e:
        return jsonify({'success':'False','error':'Missing email id'})

    if request.method=='POST':
        try:
            channel = pubsub.channel()
            result = channel.queue_declare(durable=True)
        except Exception as e:
            print "Failed to create queue "+str(e)
            channel.close()
            return jsonify({'success':'False','error':'Failed to create queue'})
        channel.close()

        apps = Application._get_collection().find({'user': email})

        if apps.count() == 0:
            Application(user=email,applications = [result.method.queue]).save()
        else:
            app_list = apps[0]['applications']
            app_list.append(result.method.queue)
            Application.objects(user=email).update(set__applications=app_list)
    else:
        apps = Application._get_collection().find({'user': email})
        return jsonify({'success':'True','app_list': apps[0]['applications']})

    return jsonify({'success':'True','app_id':result.method.queue})

@api.route('/apps/subscription',methods=['POST','DELETE'])
def subscribe_sensor():
    json_data = request.get_json()
    try:
        email = json_data['email']
        app = json_data['app']
        sensor = json_data['sensor']
    except Exception as e:
        return jsonify({'success':'False','error':'Missing parameters'})

    if app not in Application._get_collection().find({'user': email})[0]['applications']:
        return jsonify({'success':'False','error':'App id doesn\'t exist'})

    try:
        channel = pubsub.channel()
        if request.method == 'POST':
            channel.queue_bind(exchange=exchange,queue=app,routing_key=sensor)
        elif request.method == 'DELETE':
            channel.queue_unbind(exchange=exchange,queue=app,routing_key=sensor)
    except Exception as e:
        print "Failed to bind queue "+str(e)
        channel.close()
        return jsonify({'success':'False','error':'Failed to bind queue'})
    channel.close()
    return jsonify({'success':'True'})

def xstr(s):
    if s is None:
        return ""
    else:
        return str(s)

#Test API for dynamic ACL's
@api.route('/permission_change/user=<user_id>/sensor_group=<sensor_group>/permission=<permission_value>',methods=['GET'])
def permission_change(user_id,sensor_group,permission_value):
    """ Test API to dynamically modify ACL's after they have been created"""
    updated = 0
    if permission_value not in permissions:
        return jsonify({'success': 'False'})
    permission_value = permissions[permission_value]

    usergroups = r.smembers('user:{}'.format(user_id))

    for user_group in usergroups:
        permission_list = Permission.objects(user_group=user_group,\
            sensor_group=sensor_group).first()
        if permission_list!=None:
            updated += 1
            permission_list.update(set__permission=permission_value)
            r.set('permission:{}:{}'.format(user_group,\
                sensor_group),permission_value)

    if updated:
        return jsonify({'success': 'True'})
    else:
        return jsonify({'success': 'False'})

