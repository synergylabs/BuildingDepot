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

from flask import json,render_template, request, redirect, url_for, jsonify, flash
from . import api
from ..models.ds_models import *
from ..service.utils import *
from uuid import uuid4
from .. import r, influx,oauth,pubsub,exchange
from werkzeug.security import gen_salt
import sys
sys.path.append('/srv/buildingdepot')
from utils import get_user_oauth
from ..api_0_0.resources.utils import *


permissions = {"rw":"r/w","r":"r","dr":"d/r"}


@api.route('/sensor_create/name=<name>/identifier=<identifier>/building=<building>', methods=['POST'])
@oauth.require_oauth()
def sensor_create(name=None,identifier=None,building=None):
    """Check if the building the user has specified is valid and if so create
     the sensor and return the uuid"""
    for item in get_building_choices(current_app.config['NAME']):
        if building in item:
            uuid = str(uuid4())
            Sensor(name=uuid,
                       source_name=name,
                       source_identifier=identifier,
                       building=building).save()
            return jsonify({'success': 'True','uuid':uuid})
    return jsonify({'success': 'False','error':'Building does not exist'})



@api.route('/list', methods=['GET'])
@oauth.require_oauth()
def sensor_list():
    """Forms a list of sensors in the system and returns them to the user"""
    if request.method == 'GET':
        list_sensors = Sensor._get_collection().find()
        return jsonify({'data': create_response(list_sensors)})

@api.route('/data/id=<name>/email=<email>/interval=<interval>/resolution=<resolution>', methods=['GET'])
@api.route('/data/id=<name>/email=<email>/interval=<interval>', methods=['GET'])
@oauth.require_oauth()
@authenticate_acl('r')
def get_data(name,interval,email,resolution=None):
    """Reads the time series data of the sensor over the interval specified and returns it to the
       user. If resolution is also specified then data points will be averaged over the resolution
       period and returned"""
    if resolution!=None:
        data = influx.query("select mean(value) from "+"\""+name+"\""+" WHERE time > now() - "+\
            interval+" GROUP BY time("+resolution+")")
    else:
        data = influx.query("select * from "+"\""+name+"\""+" WHERE time > now() - "+interval)
    return jsonify({'data':data.raw,'response':'success'})

@api.route('/<param_1>=<value_1>/<request_type>', methods=['GET'])
@api.route('/<param_1>=<value_1>/<param_2>=<value_2>/<request_type>',methods=['GET'])
@api.route('/<param_1>=<value_1>/<param_2>=<value_2>/<param_3>=<value_3>/<request_type>',methods=['GET'])
@oauth.require_oauth()
def get_sensors_metadata(param_1,value_1,request_type,param_2=None,value_2=None,param_3=None,value_3=None):
    """ If request type is params all the sensors with the specified paramter key and values are returned,
        for request type of tags all the sensors with the matching tag key and value are searched for and
        returned, similarly for metadata"""
    if request_type == "params":
        list_sensors = Sensor._get_collection().find({param_1:value_1})
        return jsonify({'data': create_response(list_sensors)})
    elif request_type == "tags":
        if param_2==None:
            list_sensors = Sensor._get_collection().find({request_type:{'name':param_1, 'value': value_1}})
            return jsonify({'data': create_response(list_sensors)})
        elif param_3==None :
            list_sensors = Sensor._get_collection().find({request_type:{'name':param_1, 'value': value_1},request_type:{'name':param_2,'value':value_2}})
            return jsonify({'data': create_response(list_sensors)})
        else :
            list_sensors = Sensor._get_collection().find({request_type:{'name':param_1,'value': value_1},request_type:{'name':param_2,'value':value_2},request_type:{'name':param_3,'value':value_3}})
            return jsonify({'data': create_response(list_sensors)})
    elif request_type == "metadata":
        list_sensors = Sensor._get_collection().find({request_type+"."+param_1:value_1})
        return jsonify({'data': create_response(list_sensors)})

def create_json(sensor):
    """Simple function that creates a json object to return for each sensor"""
    json_object = { 'building': sensor['building'],
            'name' : sensor['name'],
            'tags' : sensor['tags'],
            'metadata' : sensor['metadata'],
            'source_identifier' : sensor['source_identifier'],
            'source_name' : sensor['source_name']
            }
    return json_object

def create_response(sensor_list):
    """Iterates over the list and generates a json response of sensors list"""
    sensor_dict = dict()
    for index,sensor in enumerate(sensor_list,start=1):
        json_temp = create_json(sensor)
        key = "sensor_"+str(index)
        sensor_dict[key] = json_temp
    return sensor_dict

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


@api.route('/data/id=<name>/email=<email>/timeseries', methods=['POST'],endpoint='sensor_timeseries')
@oauth.require_oauth()
@authenticate_acl('r/w')
def sensor_timeseries(name,email):
    """Parses the data sent in the request and posts it to the timeseries data of the
       sensorpoint with uuid <name> in InfluxDB"""
    points = [[int(pair['time']), pair['value']] for pair in request.get_json()['data']]

    try:
        value_type = request.get_json()['value_type']
    except KeyError:
        value_type='value'
    data_points = []

    #Parse through all the received data and format it to write to the DB
    for pair in request.get_json()['data']:
        temp_dict = {}
        temp_dict['measurement'] = name
        temp_dict['fields'] = {
                                'timestamp' : pair['time'],
                                'value' : pair['value']
                            }
        data_points.append(temp_dict)

    #Write to db
    influx.write_points(data_points)
    return jsonify({'success': 'True'})

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


@api.route('/sensorgroup/<name>/tags', methods=['GET', 'POST'])
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


@api.route('/usergroup_create/name=<name>/description=<description>', methods=['POST'])
@api.route('/usergroup_create/name=<name>', methods=['POST'])
def usergroup_create(name,description=None):
    #Create the usergroup
    if name == None or name == "":
        return jsonify({'success':'False','error':'No Name'})
    else:
        UserGroup(name=xstr(name),
                    description=xstr(description)).save()
        return jsonify({'success':'True'})

@api.route('/sensorgroup_create/name=<name>/building=<building>/description=<description>', methods=['POST'])
@api.route('/sensorgroup_create/name=<name>/building=<building>', methods=['POST'])
def sensorgroup_create(name,building,description=None):
    #Create the sensorgroup
    if name == None or name == "":
        return jsonify({'success':'False','error':'No Name'})

    #Get the list of buildings and verify that the one specified in the
    #request exists
    buildings_list = get_building_choices(current_app.config['NAME'])
    for item in buildings_list:
        if building in item:
            SensorGroup(name=xstr(name),building=xstr(building),
                description=xstr(description)).save()
            return jsonify({'success':'True'})

    return jsonify({'success':'False','error':'Building does not exist'})

@api.route('/usergroup/<name>/users', methods=['GET', 'POST'])
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

