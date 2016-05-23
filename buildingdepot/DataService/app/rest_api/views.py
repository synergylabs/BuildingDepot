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

from flask import json, render_template, abort, session
from flask import request, redirect, url_for, jsonify, flash
from . import api
from ..models.ds_models import *
from ..service.utils import *
from uuid import uuid4
from .. import r, influx, oauth, exchange, permissions
from werkzeug.security import gen_salt
import sys, time, influxdb, urllib, traceback, pika

sys.path.append('/srv/buildingdepot')
from utils import get_user_oauth
from ..api_0_0.resources.utils import *
from ..api_0_0.resources.acl_cache import invalidate_user,invalidate_permission

@api.route('/sensor/<name>', methods=['GET'])
@api.route('/sensor', methods=['POST'])
@oauth.require_oauth()
def sensor_create(name=None):
    '''Check if the building the user has specified is valid and if so create
    the sensor and return the uuid
    For GET:
    Args as data:
        name : <name of sensor>

    Returns (JSON):
        {
            'building': <name of building in which sensor is present>,
            'name' : <sensor uuid>,
            'tags' : tags_owned,
            'metadata' : metadata,
            'source_identifier' : str(sensor.source_identifier),
            'source_name' : str(sensor.source_name)
        }

    For POST:
    Args as data:
        "name":<name-of-sensor>
        "building":<building in which sensor is present>
        "identifier":<identifier for sensor>

    Returns (JSON) :
        {
            "success": <True or False>
            "uuid" : <uuid of sensor if created>
            "error": <details of an error if it happends>
        }
    '''
    if request.method == 'POST':
        data = request.get_json()
        try:
            building = data['building']
        except KeyError:
            return jsonify({'success': 'False', 'error': 'Missing parameters'})

        sensor_name = data.get('name')
        identifier = data.get('identifier')
        email = get_email()

        for item in get_building_choices(current_app.config['NAME']):
            if building in item:
                uuid = str(uuid4())
                Sensor(name=uuid,
                       source_name=xstr(sensor_name),
                       source_identifier=xstr(identifier),
                       building=building,
                       owner = email).save()
                r.set('owner:{}'.format(uuid),email)
                return jsonify({'success': 'True', 'uuid': uuid})
        return jsonify({'success': 'False', 'error': 'Building does not exist'})
    elif request.method == 'GET':
        if name is None:
            return jsonify({'success': 'False', 'error': 'Missing parameters'})
        sensor = Sensor.objects(name=name).first()
        if sensor is None:
            return jsonify({'success': 'False', 'error': 'Sensor doesn\'t exist'})
        tags_owned = [{'name': tag.name, 'value': tag.value} for tag in sensor.tags]
        metadata = Sensor._get_collection().find({'name': name}, {'metadata': 1, '_id': 0})[0]['metadata']
        metadata = [{'name': key, 'value': val} for key, val in metadata.iteritems()]
        return jsonify({'building': str(sensor.building),
                        'name': str(sensor.name),
                        'tags': tags_owned,
                        'metadata': metadata,
                        'source_identifier': str(sensor.source_identifier),
                        'source_name': str(sensor.source_name)
                        })


@api.route('/sensor/<name>/timeseries', methods=['GET'],endpoint="get_data")
@oauth.require_oauth()
@authenticate_acl('r')
def get_data(name):
    """Reads the time series data of the sensor over the interval specified and returns it to the
       user. If resolution is also specified then data points will be averaged over the resolution
       period and returned

       Args as data:
        "name" : <sensor uuid>
        "start_time" : <unix timestamp of start time>
        "end_time" : <unix timestamp of end time>
        "resolution" : <optional resolution can be specified to scale down data"

       Returns (JSON):
       {
            "data": {
                    "series" : [
                        "columns" : [column definitions]
                    ]
                    "name": <sensor-uuid>
                    "values" : [list of sensor values]
            }
            "success" : <True or False>
       }
       """

    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    resolution = request.args.get('resolution')

    if not all([start_time,end_time]):
        return jsonify({'success':'False','error':'Missing parameters'})

    if resolution != None:
        try:
            data = influx.query(
                'select mean(value) from "' + name + '" where (time>\'' + timestamp_to_time_string(float(start_time)) \
                + '\' and time<\'' + timestamp_to_time_string(
                    float(end_time)) + '\')' + " GROUP BY time(" + resolution + ")")
        except influxdb.exceptions.InfluxDBClientError:
            return jsonify({'success':'False','error':'Too many points for this resolution'})
    else:
        data = influx.query('select * from "' + name + '" where time>\''+ timestamp_to_time_string(float(start_time))\
         +'\' and time<\'' + timestamp_to_time_string(float(end_time)) +'\'')
    return jsonify({'success':'True','data':data.raw})

def timestamp_to_time_string(t):
    '''Converts a unix timestamp to a string representation of the timestamp
    Args:
        t: A unix timestamp float
    Returns
        A string representation of the timestamp
    '''
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t)) + str(t - int(t))[1:10] + 'Z'


@api.route('/sensor/list', methods=['GET'])
@oauth.require_oauth()
def get_sensors_metadata():
    """ If request type is params all the sensors with the specified paramter key and values are returned,
        for request type of tags all the sensors with the matching tag key and value are searched for and
        returned, similarly for metadata

        Args as data:

        "filter" : <Type of filter e.g. tags or metadata>
        "param": "value"

        Returns (JSON):
        {
          "data": [
            {
              "building": <building name>,
              "metadata": {
                    "metadata-name":"metadata value
                    .
                    .
                    <metadata key value pairs>
              },
              "name": <uuid of sensor>,
              "source_identifier": <identifier of sensor>,
              "source_name": <Sensor source name>,
              "tags": [
                {
                  "name": <name of tag>,
                  "value": <value of tag>
                }
                .
                .
                .
                <tag key value pairs>
              ]
            }
          ]
        }
    """
    request_type = request.args.get('filter')

    if (request_type is None) or (len(request.args) < 2):
        return jsonify({'success': 'False', 'error': 'Missing parameters'})

    for key, val in request.args.iteritems():
        if key != 'filter':
            param = urllib.unquote(key).decode('utf8')
            value = urllib.unquote(val).decode('utf8')
            print param, value

    if request_type == "params":
        list_sensors = Sensor._get_collection().find({param: value})
        return jsonify({'data': create_response(list_sensors)})
    elif request_type == "tags":
        list_sensors = Sensor._get_collection().find({request_type: {'name': param, 'value': value}})
        return jsonify({'data': create_response(list_sensors)})
    elif request_type == "metadata":
        list_sensors = Sensor._get_collection().find({request_type + "." + param: value})
        return jsonify({'data': create_response(list_sensors)})


def create_json(sensor):
    """Simple function that creates a json object to return for each sensor
    Args as data:
    sensor object retrieved from MongoDB

    Returns:
    {
        Formatted sensor object as below
    }
    """
    json_object = { 'building': sensor.get('building'),
            'name' : sensor.get('name'),
            'tags' : sensor.get('tags'),
            'metadata' : sensor.get('metadata'),
            'source_identifier' : sensor.get('source_identifier'),
            'source_name' : sensor.get('source_name')
            }
    return json_object


def create_response(sensors):
    """Iterates over the list and generates a json response of sensors list
    Args as data:
    list of sensor retrieved from MongoDB


    Returns:
    {
        List of formatted sensor objects
    }
    """
    sensor_list = []
    for sensor in sensors:
        json_temp = create_json(sensor)
        sensor_list.append(json_temp)
    return sensor_list


@api.route('/sensor/<name>/metadata', methods=['GET', 'POST'])
@oauth.require_oauth()
def sensor_metadata(name):
    """For the specified sensor returns all the metadata attached to it in a json response

    For GET request:
    Args as data:
    "name": <sensor-uuid>

    Returns (JSON):
    {
      "data": [
               {
                  "name": <name of metadata>,
                  "value": <value of metadata>"
               },
               .
               .
               .

              ]
    }

    For POST Request:
    Args as data:
    "name": <sensor uuid>

    Following data in JSON:
    {
      "data": [
               {
                  "name": <name of metadata>,
                  "value": <value of metadata>"
               },
               .
               .
               .

              ]
    }

    Returns (JSON):
    {
        "success": <True or false>
    }
    """
    if request.method == 'GET':
        metadata = Sensor._get_collection().find({'name': name}, {'metadata': 1, '_id': 0})[0]['metadata']
        metadata = [{'name': key, 'value': val} for key, val in metadata.iteritems()]
        return jsonify({'data': metadata})
    # For a POST request upadtes the metadata
    else:
        metadata = {pair['name']: pair['value'] for pair in request.get_json()['data'] if pair['name'] != ''}
        building = Sensor.objects(name=name).first()
        building.update(set__metadata=metadata)
        return jsonify({'success': 'True'})


@api.route('/sensor/<name>/subscribers', methods=['GET', 'POST'])
@oauth.require_oauth()
def sensor_subscribers(name):
    """ Either updates or retrieves the list of subscribers for the sensor with uuid
        <name> depending on whether the request is GET or POST

    For GET request:
    Args as data:
    "name" : <sensor-uuid>

    Returns (JSON) :
    {
        "subscribers":[ list of user ids,....]
    }

    For POST request:
    Args as data:
    "name" : <sensor-uuid>

    Following data in JSON:
    {
        "data":[ list of user ids,....]
    }

    Returns (JSON) :
    {
        "success": <True or False>
    }
    """

    if request.method == 'GET':
        subscribers = r.smembers('subscribers:{}'.format(name))
        data = [{'email': subscriber} for subscriber in subscribers]
        return jsonify({'subscribers': data})
    else:
        new_subscribers = [subscriber['email'] for subscriber in request.get_json()['data']]
        if validate_users(new_subscribers):
            old_subscribers = r.smembers('subscribers:{}'.format(name))
            # Finds the new users that have been added and the users that have
            # been deleted in order to update the cache
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
                "sensor_id":
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

    pubsub = connect_broker()
    if pubsub:
        try:
            channel = pubsub.channel()
        except Exception as e:
            print "Failed to open channel"+" error"+str(e)

    try:
        json = request.get_json()
        points = []
        for sensor in json:
            # check a user has permission
            unauthorised_sensor = []
            if permission(sensor['sensor_id']) == 'r/w':
                for sample in sensor['samples']:
                    dic = {
                        'measurement': sensor['sensor_id'],
                        'time': timestamp_to_time_string(sample['time']),
                        'fields': {
                            'inserted_at': timestamp_to_time_string(time.time()),
                            'value': sample['value']
                        }
                    }
                    points.append(dic)
                try:
                    channel.basic_publish(exchange=exchange,routing_key=sensor['sensor_id'],\
                        body=str(dic))
                except Exception as e:
                    print "Failed to write to broker "+str(e)
            else:
                unauthorised_sensor.append(sensor['sensor_id'])
    except KeyError:
        abort(400)

    result = influx.write_points(points)

    dic = {}

    if result:
        if len(unauthorised_sensor) > 0:
            dic['success'] = 'False'
            dic['unauthorised_sensor'] = unauthorised_sensor
            dic['error'] = 'Unauthorised sensors present'
        else:
            dic['success'] = 'True'
    else:
        dic['success'] = 'False'
        dic['error'] = 'Error in writing in InfluxDB'

    if pubsub:
        try:
            channel.close()
            pubsub.close()
        except Exception as e:
            print "Failed to end RabbitMQ session"+str(e)

    return jsonString(dic)


def jsonString(obj, pretty=False):
    if pretty == True:
        return json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': ')) + '\n'
    else:
        return json.dumps(obj)


@api.route('/sensor/<name>/tags',methods=['GET'])
@oauth.require_oauth()
def sensor_tags(name):
    """Returns the list of tags that are attached to the sensor with the uuid <name>
    Args as data:
    "name" : <sensor-uuid>

    Returns (JSON):
    {
      "tags": {
               "Tag Name": [ List of eligible values],
               .
               .
               .
              }, (These are the list of eligibile tags for this sensor)
      "tags_owned": [
                      {
                       "name": <Tag-Name>,
                       "value": <Tag-Value>
                      },
                      .
                      .
                      .
                    ] (These are the list of tags owned by this sensor)
    } """
    # If request is a GET then return the list of tags
    obj = Sensor.objects(name=name).first()
    tags_owned = [{'name': tag.name, 'value': tag.value} for tag in obj.tags]
    tags = get_building_tags(obj.building)
    return jsonify({'tags': tags, 'tags_owned': tags_owned})

@api.route('/sensor/<name>/tags', methods=['POST'])
@oauth.require_oauth()
@authenticate_acl('r/w/p')
def sensor_tags(name):
    """Updates the list of tags that are attached to the sensor with the uuid <name>
    Args as data:
    "name" : <sensor-uuid>

    Following data in JSON:
    {
      "data": [
               {
                "name": <Tag-Name>,
                "value": <Tag-Value>
                },
                .
                .
                .
              ]
    }

    Returns:
    {
        "success": <True or False>
    }
    """
    # If request is a POST then update the tags
    tags = request.get_json()['data']

    # cache process
    sensor = Sensor.objects(name=name).first()
    building = sensor.building
    # Get old tags and new tags and find the list of tags that have to be added and deleted
    # based on the response from get_add_delete
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
    # Also update in the cache the sensorgroups and tags that this specific sensor is attached to
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

    pipe.delete(sensor)
    pipe.execute()

    return jsonify({'success': 'True'})


@api.route('/sensor_group/<name>/tags', methods=['GET', 'POST'])
@oauth.require_oauth()
def sensorgroup_tags(name):
    """Returns/Updates the list of tags that are attached to the sensorgroup <name>
    For GET request:
    Args as data:
    "name" : <Name of SensorGroup>

    Returns (JSON):
    {
      "tags": {
               "Tag Name": [ List of eligible values],
               .
               .
               .
              }, (These are the list of eligibile tags for this sensor)
      "tags_owned": [
                      {
                       "name": <Tag-Name>,
                       "value": <Tag-Value>
                      },
                      .
                      .
                      .
                    ] (These are the list of tags owned by this sensor)
    }

    For POST request:
    Args as data:
    "name" : <Name of SensorGroup>

    Following data in JSON:
    {
      "data": [
               {
                "name": <Tag-Name>,
                "value": <Tag-Value>
                },
                .
                .
                .
              ]
    }

    Returns:
    {
        "success" : <True or False>
    }

    """
    if request.method == 'GET':
        # Retrieve the list
        obj = SensorGroup.objects(name=name).first()
        tags_owned = [{'name': tag.name, 'value': tag.value} for tag in obj.tags]
        tags = get_building_tags(obj.building)
        return jsonify({'tags': tags, 'tags_owned': tags_owned})
    else:
        if Permission.objects(sensor_group=name).first() is not None:
            return jsonify({'success':'False','error':"""Sensor group tags cannot be edited.
                Already being used for permissions"""})
        tags = request.get_json()['data']
        # cache process
        sensorgroup = SensorGroup.objects(name=name).first()
        old = ['tag-sensorgroup:{}:{}:{}'.format(sensorgroup.building, tag.name, tag.value) for tag in sensorgroup.tags]
        new = ['tag-sensorgroup:{}:{}:{}'.format(sensorgroup.building, tag['name'], tag['value']) for tag in tags]
        added, deleted = get_add_delete(old, new)
        pipe = r.pipeline()
        for tag in added:
            pipe.sadd(tag, name)
        for tag in deleted:
            pipe.srem(tag, name)
        pipe.set('tag-count:{}'.format(name), len(new))
        # recalculate the sensors that this sensorgroup contains
        tags_owned = ['tag:{}:{}:{}'.format(sensorgroup.building, tag['name'], tag['value']) for tag in tags]

        old_sensors = r.smembers('sensorgroup:{}'.format(name))
        new_sensors = r.sinter(tags_owned) if len(tags_owned) > 0 else []
        added, deleted = get_add_delete(old_sensors, new_sensors)

        for sensor_name in added:
            pipe.sadd('sensor:{}'.format(sensor_name), name)
        for sensor_name in deleted:
            pipe.srem('sensor:{}'.format(sensor_name), name)
            pipe.delete(sensor_name)

        r.delete('sensorgroup:{}'.format(name))
        for item in new_sensors:
            pipe.sadd('sensorgroup:{}'.format(name), item)
        pipe.execute()
        # cache process done
        SensorGroup.objects(name=name).update(set__tags=tags)
        return jsonify({'success': 'True'})


@api.route('/user_group', methods=['POST'])
@oauth.require_oauth()
def usergroup_create():
    """
    Args as data:
    name = <name of user group>
    description = <description for group>

    Returns (JSON) :
    {
        "success" : <True or False>
        "error" : <If False then error will be returned>
    }
    """
    name = request.args.get('name')
    description = request.args.get('description')
    if name is None:
        return jsonify({'success': 'False', 'error': 'Missing parameters'})
    UserGroup(name=xstr(name),
              description=xstr(description)).save()
    return jsonify({'success': 'True'})


@api.route('/sensor_group', methods=['POST'])
@oauth.require_oauth()
def sensorgroup_create():
    """
    Args as data:
    name = <name of user group>
    description = <description for group>
    building = <building in which sensor group will be created>

    Returns (JSON) :
    {
        "success" : <True or False>
        "error" : <If False then error will be returned>
    }
    """
    name = request.args.get('name')
    building = request.args.get('building')
    description = request.args.get('description')

    if not all([name, building]):
        return jsonify({'success': 'False', 'error': 'Missing parameters'})

    # Get the list of buildings and verify that the one specified in the
    # request exists
    buildings_list = get_building_choices(current_app.config['NAME'])
    for item in buildings_list:
        if building in item:
            SensorGroup(name=xstr(name), building=xstr(building),
                        description=xstr(description)).save()
            return jsonify({'success': 'True'})

    return jsonify({'success': 'False', 'error': 'Building does not exist'})


@api.route('/user_group/<name>/users', methods=['GET', 'POST'])
@oauth.require_oauth()
def usergroup_users(name):
    """ Updates/Returns the lists of users that are attached to the usergroup <name>
    For GET request:
    Args as data:
    name = <name of user group>

    Returns (JSON):
    {
        "users" : [user-id's,.......]
    }

    For POST request:
    Args as data:
    name = <name of user group>

    Following data as JSON:
    {
        "users" : [user-id's,.......]
    }

    Returns (JSON):
    {
        "success" : <True or False>
    }
    """
    if request.method == 'GET':
        obj = UserGroup.objects(name=name).first()
        return jsonify({'users': obj.users})
    else:
        emails = request.get_json()['data']
        if validate_users(emails):
            # cache process
            user_group = UserGroup.objects(name=name).first()
            # Recalculate the list of users that have to be added and
            # removed from this group based on the new list received
            added, deleted = get_add_delete(user_group.users, emails)
            pipe = r.pipeline()
            for user in added:
                pipe.sadd('user:{}'.format(user), user_group.name)
                invalidate_user(name,user)
            for user in deleted:
                pipe.srem('user:{}'.format(user), user_group.name)
                invalidate_user(name,user)
            pipe.execute()
            # cache process done
            UserGroup.objects(name=name).update(set__users=emails)
            return jsonify({'success': 'True'})
        return jsonify({'success': 'False', 'error': 'One or more users not registered'})


@api.route('/apps',methods=['GET','POST'])
@oauth.require_oauth()
def register_app():
    email = get_email()
    if request.method == 'POST':
        json_data = request.get_json()
        try:
            name = json_data['name']
        except KeyError:
            return jsonify({'success': 'False', 'error': 'Missing parameters'})
        apps = Application._get_collection().find({'user': email})

        if apps.count()!=0:
            app_list = apps[0]['apps']
            for app in app_list:
                if name==app['name']:
                    return jsonify({'success':'True','app_id':app['value']})

        pubsub = connect_broker()
        if pubsub is None:
            return jsonify({'success': 'False', 'error': 'Failed to connect to broker'})

        try:
            channel = pubsub.channel()
            result = channel.queue_declare(durable=True)
        except Exception as e:
            print "Failed to create queue " + str(e)
            print traceback.print_exc()
            if channel:
                channel.close()
            return jsonify({'success':'False','error':'Failed to create queue'})

        if apps.count() == 0:
            Application(user=email, apps=[{'name':name,'value':result.method.queue}]).save()
        else:
            app_list.append({'name':name,'value':result.method.queue})
            Application.objects(user=email).update(set__apps=app_list)
    else:
        if email is None:
            return jsonify({'success': 'False', 'error': 'Missing parameters'})
        apps = Application._get_collection().find({'user': email})
        return jsonify({'success': 'True', 'app_list': apps[0]['apps']})

    if pubsub:
        try:
            channel.close()
            pubsub.close()
        except Exception as e:
            print "Failed to end RabbitMQ session"+str(e)

    return jsonify({'success': 'True', 'app_id': result.method.queue})

def get_email():
    headers = request.headers
    token = headers['Authorization'].split()[1]
    return Token.objects(access_token=token).first().email

@api.route('/apps/subscription',methods=['POST','DELETE'])
@oauth.require_oauth()
def subscribe_sensor():
    json_data = request.get_json()
    email = get_email()
    try:
        app_id = json_data['app']
        sensor = json_data['sensor']
    except Exception as e:
        return jsonify({'success': 'False', 'error': 'Missing parameters'})

    app_list = Application._get_collection().find({'user': email})[0]['apps']

    pubsub = connect_broker()
    if pubsub is None:
        return jsonify({'success': 'False', 'error': 'Failed to connect to broker'})

    for app in app_list:
        if app_id == app['value']:
            try:
                channel = pubsub.channel()
                if request.method == 'POST':
                    channel.queue_bind(exchange=exchange, queue=app['value'], routing_key=sensor)
                elif request.method == 'DELETE':
                    channel.queue_unbind(exchange=exchange, queue=app['value'], routing_key=sensor)
            except Exception as e:
                print "Failed to bind queue " + str(e)
                print traceback.print_exc()
                return jsonify({'success': 'False', 'error': 'Failed to bind queue'})

            if pubsub:
                try:
                    channel.close()
                    pubsub.close()
                except Exception as e:
                    print "Failed to end RabbitMQ session"+str(e)

            return jsonify({'success': 'True'})

    return jsonify({'success': 'False', 'error': 'App id doesn\'t exist'})

@api.route('/permission',methods=['GET','POST'])
@oauth.require_oauth()
def create_permission():
    if request.method=='GET':
        user_group = request.args.get('user_group')
        sensor_group = request.args.get('sensor_group')
        if not all([user_group,sensor_group]):
            return jsonify({'success':'False','error':'Missing parameters'})
        else:
            permission = Permission.objects(user_group=user_group,sensor_group=sensor_group).first()
            if permission is None:
                return jsonify({'success':'False','error':'Permission doesn\'t exist'})
            else:
                return jsonify({'success':'True','permission':permission.permission})
    elif request.method=='POST':
        data = request.get_json()
        try:
            sensor_group = data['sensor_group']
            user_group = data['user_group']
            permission = data['permission']
        except KeyError:
            return jsonify({'success':'False','error':'Missing parameters'})

        if UserGroup.objects(name=user_group).first() is None:
            return jsonify({'success':'False','error':'User group doesn\'t exist'})
        if SensorGroup.objects(name=sensor_group).first() is None:
            return jsonify({'success':'False','error':'Sensor group doesn\'t exist'})
        if permissions.get(permission) is None:
            return jsonify({'success':'False','error':'Permission value doesn\'t exist'})

        if authorize_user(user_group,sensor_group):
            if Permission.objects(user_group=user_group,sensor_group=sensor_group).first() is not None:
                Permission.objects(user_group=user_group,
                    sensor_group=sensor_group).first().update(permission=permissions.get(permission))
            else:
                Permission(user_group=user_group,sensor_group=sensor_group,
                    permission=permissions.get(permission)).save()
            invalidate_permission(sensor_group)
            r.set('permission:{}:{}'.format(user_group,sensor_group),permissions.get(permission))
            return jsonify({'success':'True'})
        else:
            return jsonify({'success':'False','error':'Unauthorised sensors in sensor group'})

@api.route('/permission',methods=['DELETE'])
@oauth.require_oauth()
def delete_permission():
    if request.method=='DELETE':
        user_group = request.args.get('user_group')
        sensor_group = request.args.get('sensor_group')
        if not all([user_group,sensor_group]):
            return jsonify({'success':'False','error':'Missing parameters'})
        else:
            if authorize_user(user_group,sensor_group):
                permission = Permission.objects(user_group = user_group,sensor_group = sensor_group)
                if permission.first() is None:
                    return jsonify({'success':'False','error':'Permission is not defined'})
                else:
                    permission.first().delete()
                    r.delete('permission:{}:{}'.format(user_group,sensor_group))
                    invalidate_permission(sensor_group)
                    return jsonify({'success':'True','error':'Permission deleted'})
            else:
                return jsonify({'success':'False','error':"""You are not authorized to delete
                    this permission"""})

def connect_broker():
    try:
        pubsub = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = pubsub.channel()
        channel.exchange_declare(exchange=exchange,type='direct')
        channel.close()
        return pubsub
    except Exception as e:
        print "Failed to open connection to broker "+str(e)
        return None

def xstr(s):
    if s is None:
        return ""
    else:
        return str(s)

# Test API for dynamic ACL's
@api.route('/permission_change/user=<user_id>/sensor_group=<sensor_group>/permission=<permission_value>',
           methods=['GET'])
def permission_change(user_id, sensor_group, permission_value):
    """ Test API to dynamically modify ACL's after they have been created"""
    updated = 0
    if permission_value not in permissions:
        return jsonify({'success': 'False'})
    permission_value = permissions[permission_value]

    usergroups = r.smembers('user:{}'.format(user_id))

    for user_group in usergroups:
        permission_list = Permission.objects(user_group=user_group, \
                                             sensor_group=sensor_group).first()
        if permission_list != None:
            updated += 1
            permission_list.update(set__permission=permission_value)
            r.set('permission:{}:{}'.format(user_group, \
                                            sensor_group), permission_value)
    if updated:
        return jsonify({'success': 'True'})
    else:
        return jsonify({'success': 'False'})
