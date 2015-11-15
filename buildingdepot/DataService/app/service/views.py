from flask import json,render_template, request, redirect, url_for, jsonify, flash
from . import service
from ..models.ds_models import *
from .forms import *
from .utils import *
from uuid import uuid4

from .. import r, influx
import sys
sys.path.append('/srv/buildingdepot')
from OAuth2Server.app import *
from utils import get_user_oauth 
from ..api_0_0.resources.utils import *


permissions = {"rw":"r/w","r":"r","dr":"d/r"}

@service.route('/sensor', methods=['GET', 'POST'])
def sensor():
    page = request.args.get('page', 1, type=int)
    skip_size = (page-1)*PAGE_SIZE
    objs = Sensor.objects().skip(skip_size).limit(PAGE_SIZE)
    for obj in objs:
        obj.can_delete = True

    form = SensorForm()
    form.building.choices = get_building_choices(current_app.config['NAME'])
    if form.validate_on_submit():
        Sensor(name=str(uuid4()),
               source_name=str(form.source_name.data),
               source_identifier=str(form.source_identifier.data),
               building=str(form.building.data)).save()
        return redirect(url_for('service.sensor'))
    return render_template('service/sensor.html', objs=objs, form=form)

@service.route('/api/v1/list', methods=['GET'])
@oauth.require_oauth()
def sensor_list():
    if request.method == 'GET':
	list_sensors = Sensor._get_collection().find()
	return jsonify({'data': create_response(list_sensors)})

@service.route('/api/v1/data/id=<name>/email=<email>/interval=<interval>/resolution=<resolution>/meta=<meta>', methods=['GET'])
@service.route('/api/v1/data/id=<name>/email=<email>/interval=<interval>/resolution=<resolution>', methods=['GET'])
@service.route('/api/v1/data/id=<name>/email=<email>/interval=<interval>/', methods=['GET'])
@oauth.require_oauth()
@authenticate_acl('r')
def get_data(name,interval,email,resolution=None,meta=None):
    if meta == "True" :
        metadata = Sensor._get_collection().find({'name': name}, {'metadata': 1, '_id': 0})[0]['metadata']
        sensorList = metadata['Sensor_List'].split(",")
        nameList = ""
        for element in sensorList:
            nameList+= "\""+element+"\","
        nameList = nameList[:-1]
        data = influx.query("select mean(value) from "+nameList+" WHERE time > now() - "+interval+" GROUP BY time("+resolution+")").raw
        dataDict = {}
        for series in data['series']:
            dataDict[series['name']]=series['values']
        return jsonify({'data':calculateAvg(dataDict,name)})
    elif resolution!=None:
		data = influx.query("select mean(value) from "+"\""+name+"\""+" WHERE time > now() - "+interval+" GROUP BY time("+resolution+")")
    else:
		data = influx.query("select * from "+"\""+name+"\""+" WHERE time > now() - "+interval)
    return jsonify({'data':data.raw,'response':'success'})

def calculateAvg(dataDict,name):
    numOfSeries = len(dataDict)
    numOfValues = len(dataDict.keys()[0])
    keysList = dataDict.keys()
    finalList = []
    for i in range(0,numOfValues):
        temp,counter = 0,0
        for key in keysList:
            try:
                currElement = dataDict[key][i][1]  
            except Exception:
                currElement = None
            if currElement!=None:
                temp+=currElement
                counter+=1
        if counter:
            finalList.append([dataDict[key][0][0],temp/counter])
    finalObj = {
                    "series": [
                        {
                        "columns": [
                                    "time", 
                                    "mean"
                        ], 
                        "name": name, 
                        "values": finalList
                    }
                ]
            }
    return finalObj

   
@service.route('/api/v1/<param_1>=<value_1>/<request_type>', methods=['GET'])
@service.route('/api/v1/<param_1>=<value_1>/<param_2>=<value_2>/<request_type>',methods=['GET'])
@service.route('/api/v1/<param_1>=<value_1>/<param_2>=<value_2>/<param_3>=<value_3>/<request_type>',methods=['GET'])
@oauth.require_oauth()
def get_sensors_metadata(param_1,value_1,request_type,param_2=None,value_2=None,param_3=None,value_3=None):
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
	json_object = { 'building': sensor['building'],
			'name' : sensor['name'],
			'tags' : sensor['tags'],
			'metadata' : sensor['metadata'],
			'source_identifier' : sensor['source_identifier'],
			'source_name' : sensor['source_name']
			}
	return json_object

def create_response(sensor_list):
	i=0
	sensor_dict = {}
        for sensor in sensor_list:
                json_temp = create_json(sensor)
                i+=1
                key = "sensor_"+str(i)
                sensor_dict[key] = json_temp
	return sensor_dict
	
@service.route('/sensor/<name>/metadata', methods=['GET', 'POST'])
def sensor_metadata(name):
    if request.method == 'GET':
        metadata = Sensor._get_collection().find({'name': name}, {'metadata': 1, '_id': 0})[0]['metadata']
        metadata = [{'name': key, 'value': val} for key, val in metadata.iteritems()]
        return jsonify({'data': metadata})
    else:
        metadata = {pair['name']: pair['value'] for pair in request.get_json()['data'] if pair['name'] != ''}
        building = Sensor.objects(name=name).first()
        building.update(set__metadata=metadata)
        return jsonify({'success': 'True'})


@service.route('/sensor/<name>/subscribers', methods=['GET', 'POST'])
def sensor_subscribers(name):
    if request.method == 'GET':
        subscribers = r.smembers('subscribers:{}'.format(name))
        data = [{'email': subscriber} for subscriber in subscribers]
        return jsonify({'subscribers': data})
    else:
        new_subscribers = [subscriber['email'] for subscriber in request.get_json()['data']]
        if validate_users(new_subscribers):
            old_subscribers = r.smembers('subscribers:{}'.format(name))
            added, deleted = get_add_delete(old_subscribers, new_subscribers)
            pipe = r.pipeline()
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


@service.route('/sensor/<name>/<email>/timeseries', methods=['POST'],endpoint='sensor_timeseries')
@oauth.require_oauth()
@authenticate_acl('r/w')
def sensor_timeseries(name,email):
    points = [[int(pair['time']), pair['value']] for pair in request.get_json()['data']]

    try:
        value_type = request.get_json()['value_type']
    except KeyError:
        value_type='value'
    data_points = []
    for pair in request.get_json()['data']:
        temp_dict = {}
        temp_dict['measurement'] = name
        temp_dict['fields'] = { 
                                'timestamp' : pair['time'],
                                'value' : pair['value']
                            }
        data_points.append(temp_dict)
    
    max_point = max(points)
    emails = r.smembers('subscribers:{}'.format(name))
    pipe = r.pipeline()
    for email in emails:
        pipe.set('latest_point:{}:{}'.format(name, email), '{}-{}'.format(max_point[0], max_point[1]))
    pipe.execute()

    influx.write_points(data_points)
    return jsonify({'success': 'True'})


@service.route('/sensor_delete', methods=['POST'])
def sensor_delete():
    #cache process
    sensor = Sensor.objects(name=request.form.get('name')).first()
    tags = ['tag:{}:{}:{}'.format(sensor.building, tag.name, tag.value) for tag in sensor.tags]
    pipe = r.pipeline()
    for tag in tags:
        pipe.srem(tag, sensor.name)

    deleted = [tag.replace('tag', 'tag-sensorgroup', 1) for tag in tags]
    for key in deleted:
        for name in r.smembers(key):
            pipe.srem('sensorgroup:{}'.format(name), sensor.name)

    # clean subscribers
    emails = r.smembers('subscribers:{}'.format(sensor.name))
    pipe.delete('subscribers:{}'.format(sensor.name))
    for email in emails:
        pipe.srem('subscribed_sensors:{}'.format(email), sensor.name)

    pipe.delete('sensor:{}'.format(sensor.name))
    pipe.execute()
    #cache process done

    Sensor.objects(name=sensor.name).delete()
    return redirect(url_for('service.sensor'))


@service.route('/sensor/<name>/tags', methods=['GET', 'POST'])
def sensor_tags(name):
    if request.method == 'GET':
        obj = Sensor.objects(name=name).first()
        tags_owned = [{'name': tag.name, 'value': tag.value} for tag in obj.tags]
        tags = get_building_tags(obj.building)
        return jsonify({'tags': tags, 'tags_owned': tags_owned})
    else:
        tags = request.get_json()['data']

        # cache process
        sensor = Sensor.objects(name=name).first()
        building = sensor.building
        old = ['tag:{}:{}:{}'.format(building, tag.name, tag.value) for tag in sensor.tags]
        new = ['tag:{}:{}:{}'.format(building, tag['name'], tag['value']) for tag in tags]
        added, deleted = get_add_delete(old, new)
        pipe = r.pipeline()
        for tag in added:
            pipe.sadd(tag, name)
        for tag in deleted:
            pipe.srem(tag, name)
	pipe.execute()
        # cache process done
        Sensor.objects(name=name).update(set__tags=tags)
	
        added = [tag.replace('tag', 'tag-sensorgroup', 1) for tag in added]
        deleted = [tag.replace('tag', 'tag-sensorgroup', 1) for tag in deleted]

        pipe = r.pipeline()
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


@service.route('/sensorgroup', methods=['GET', 'POST'])
def sensorgroup():
    page = request.args.get('page', 1, type=int)
    skip_size = (page-1)*PAGE_SIZE
    objs = SensorGroup.objects().skip(skip_size).limit(PAGE_SIZE)
    for obj in objs:
        obj.can_delete = True

    form = SensorGroupForm()
    form.building.choices = get_building_choices(current_app.config['NAME'])
    if form.validate_on_submit():
        SensorGroup(name=str(form.name.data),
                    description=str(form.description.data),
                    building=str(form.building.data)).save()
        return redirect(url_for('service.sensorgroup'))
    return render_template('service/sensorgroup.html', objs=objs, form=form)

@service.route('/oauth',methods=['GET','POST'])
def oauth():
    keys = []
    if request.method == 'POST':
	keys.append({"client_id":gen_salt(40),"client_secret":gen_salt(50)})
	item = Client(
        client_id=keys[0]['client_id'],
        client_secret=keys[0]['client_secret'],
         _redirect_uris=' '.join([
            'http://localhost:8000/authorized',
            'http://127.0.0.1:8000/authorized',
            'http://127.0.1:8000/authorized',
            'http://127.1:8000/authorized']),
        _default_scopes='email',
        user = request.form.get('name')).save()
    	return render_template('service/oauth.html',keys=keys)
    return render_template('service/oauth.html',keys=keys)

@service.route('/sensorgroup/<name>/tags', methods=['GET', 'POST'])
def sensorgroup_tags(name):
    if request.method == 'GET':
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


@service.route('/sensorgroup_delete', methods=['POST'])
def sensorgroup_delete():
    # cache process
    sensorgroup = SensorGroup.objects(name=request.form.get('name')).first()
    pipe = r.pipeline()

    for sensor_name in r.smembers('sensorgroup:{}'.format(sensorgroup.name)):
        pipe.srem('sensor:{}'.format(sensor_name), sensorgroup.name)

    pipe.delete('sensorgroup:{}'.format(sensorgroup.name))
    for tag in sensorgroup.tags:
        pipe.srem('tag-sensorgroup:{}:{}:{}'.format(sensorgroup.building, tag.name, tag.value), sensorgroup.name)
    pipe.delete('tag-count:{}'.format(sensorgroup.name))
    pipe.execute()
    # cache process done

    SensorGroup.objects(name=sensorgroup.name).delete()
    return redirect(url_for('service.sensorgroup'))


@service.route('/usergroup', methods=['GET', 'POST'])
def usergroup():
    page = request.args.get('page', 1, type=int)
    skip_size = (page-1)*PAGE_SIZE
    objs = UserGroup.objects().skip(skip_size).limit(PAGE_SIZE)
    for obj in objs:
        obj.can_delete = True

    form = UserGroupForm()
    if form.validate_on_submit():
        UserGroup(name=str(form.name.data),
                  description=str(form.description.data)).save()
        return redirect(url_for('service.usergroup'))
    return render_template('service/usergroup.html', objs=objs, form=form)


@service.route('/usergroup_delete', methods=['POST'])
def usergroup_delete():
    # cahce process
    name = request.form.get('name')
    users = UserGroup.objects(name=request.form.get('name')).first().users
    pipe = r.pipeline()
    for user in users:
        pipe.srem('user:{}'.format(user), name)
    pipe.execute()
    # cahce process done

    UserGroup.objects(name=name).delete()
    return redirect(url_for('service.usergroup'))


@service.route('/usergroup/<name>/users', methods=['GET', 'POST'])
def usergroup_users(name):
    if request.method == 'GET':
        obj = UserGroup.objects(name=name).first()
        return jsonify({'users': obj.users})
    else:
        emails = request.get_json()['data']
        if validate_users(emails):
            # cache process
            user_group = UserGroup.objects(name=name).first()
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
        return jsonify({'success': 'False'})


@service.route('/permission', methods=['GET', 'POST'])
def permission():
    page = request.args.get('page', 1, type=int)
    skip_size = (page-1)*PAGE_SIZE
    objs = Permission.objects().skip(skip_size).limit(PAGE_SIZE)
    for obj in objs:
        obj.can_delete = True

    form = PermissionForm()
    form.user_group.choices = sorted([(obj.name, obj.name) for obj in UserGroup.objects])
    form.sensor_group.choices = sorted([(obj.name, obj.name) for obj in SensorGroup.objects])
    if form.validate_on_submit():
        if Permission.objects(user_group=form.user_group.data, sensor_group=form.sensor_group.data).first() is not None:
            flash('There is already permission pair {} - {} specified'.format(
                form.user_group.data, form.sensor_group.data))
            return redirect(url_for('service.permission'))
        Permission(user_group=str(form.user_group.data),
                   sensor_group=str(form.sensor_group.data),
                   permission=form.permission.data).save()
        r.set('permission:{}:{}'.format(form.user_group.data, form.sensor_group.data), form.permission.data)
        return redirect(url_for('service.permission'))
    return render_template('service/permission.html', objs=objs, form=form)


@service.route('/permission_delete', methods=['POST'])
def permission_delete():
    code = request.form.get('name').split(':-:')
    Permission.objects(user_group=code[0], sensor_group=code[1]).delete()
    r.delete('permission:{}:{}'.format(code[0], code[1]))
    return redirect(url_for('service.permission'))


@service.route('/permission_query', methods=['GET', 'POST'])
def permission_query():
    form = PermissionQueryForm()
    res = None
    if form.validate_on_submit():
        if not validate_users([form.user.data]):
            flash('User {} does not exist'.format(form.user.data))
            return render_template('service/query.html', form=form, res=res)

        sensor = Sensor.objects(name=form.sensor.data).first()
        if sensor is None:
            flash('Sensor {} does not exist'.format(form.sensor.data))
            return render_template('service/query.html', form=form, res=res)

        usergroups = r.smembers('user:{}'.format(form.user.data))
        sensorgroups = r.smembers('sensor:{}'.format(form.sensor.data))

        for usergroup in usergroups:
            for sensorgroup in sensorgroups:
                res = r.get('permission:{}:{}'.format(usergroup, sensorgroup))
                if res == 'r/w' or res == 'd/r':
                    return render_template('service/query.html', form=form, res=res)
        if res == 'r':
            return render_template('service/query.html', form=form, res=res)

        sensor_tags = ['{}:{}'.format(tag.name, tag.value) for tag in sensor.tags]
        res = get_permission(sensor_tags, sensor.building, form.user.data)

    return render_template('service/query.html', form=form, res=res)

#Test API for dynamic ACL's
@service.route('/permission_change/user=<user_id>/sensor_group=<sensor_group>/permission=<permission_value>',methods=['GET'])
def permission_change(user_id,sensor_group,permission_value):

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

