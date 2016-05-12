"""
DataService.service.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains all the definitions for the frontend functions. Any action on the
Web interface will generate a call to one of these functions that renders
a html page.

For example opening up http://localhost:81/service/sensor on your installation
of BD will call the sensor() function

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask import json, render_template, request
from flask import session, redirect, url_for, jsonify, flash
from . import service
from ..models.ds_models import *
from .forms import *
from ..rest_api.utils import *
from uuid import uuid4
from .. import r, influx, oauth
from werkzeug.security import gen_salt
import sys
import math

sys.path.append('/srv/buildingdepot')
from utils import get_user_oauth
from ..api_0_0.resources.utils import *

permissions = {"rw": "r/w", "r": "r", "dr": "d/r"}


@service.route('/sensor', methods=['GET', 'POST'])
def sensor():
    # Show the user PAGE_SIZE number of sensors on each page
    page = request.args.get('page', 1, type=int)
    skip_size = (page - 1) * PAGE_SIZE
    objs = Sensor.objects().skip(skip_size).limit(PAGE_SIZE)
    for obj in objs:
        obj.can_delete = True
    total = len(Sensor.objects())
    if (total):
        pages = int(math.ceil(float(total) / PAGE_SIZE))
    else:
        pages = 0
    form = SensorForm()
    # Get the list of valid buildings for this DataService
    form.building.choices = get_building_choices(current_app.config['NAME'])
    # Create a Sensor
    if form.validate_on_submit():
        uuid = str(uuid4())
        Sensor(name=uuid,
               source_name=str(form.source_name.data),
               source_identifier=str(form.source_identifier.data),
               building=str(form.building.data),
               owner=session['email']).save()
        r.set(uuid, session['email'])
        return redirect(url_for('service.sensor'))
    return render_template('service/sensor.html', objs=objs, form=form, total=total,
                           pages=pages, current_page=page, pagesize=PAGE_SIZE)


@service.route('/sensor_delete', methods=['POST'])
def sensor_delete():
    # cache process
    sensor = Sensor.objects(name=request.form.get('name')).first()
    tags = ['tag:{}:{}:{}'.format(sensor.building, tag.name, tag.value) for tag in sensor.tags]
    pipe = r.pipeline()
    for tag in tags:
        pipe.srem(tag, sensor.name)

    # Remove the sensor from the sensorgroup caching
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
    r.delete(request.form.get('name'))
    # cache process done

    Sensor.objects(name=sensor.name).delete()
    return redirect(url_for('service.sensor'))


@service.route('/sensorgroup', methods=['GET', 'POST'])
def sensorgroup():
    page = request.args.get('page', 1, type=int)
    skip_size = (page - 1) * PAGE_SIZE
    objs = SensorGroup.objects().skip(skip_size).limit(PAGE_SIZE)
    for obj in objs:
        obj.can_delete = True

    form = SensorGroupForm()
    # Get list of valid buildings for this DataService and create a sensorgroup
    form.building.choices = get_building_choices(current_app.config['NAME'])
    if form.validate_on_submit():
        SensorGroup(name=str(form.name.data),
                    description=str(form.description.data),
                    building=str(form.building.data)).save()
        return redirect(url_for('service.sensorgroup'))
    return render_template('service/sensorgroup.html', objs=objs, form=form)


@service.route('/oauth_gen', methods=['GET', 'POST'])
def oauth_gen():
    keys = []
    """If a post request is made then generate a client id and secret key
       that the user can use later to generate an OAuth token"""
    if request.method == 'POST':
        keys.append({"client_id": gen_salt(40), "client_secret": gen_salt(50)})
        item = Client(
            client_id=keys[0]['client_id'],
            client_secret=keys[0]['client_secret'],
            _redirect_uris=' '.join([
                'http://localhost:8000/authorized',
                'http://127.0.0.1:8000/authorized',
                'http://127.0.1:8000/authorized',
                'http://127.1:8000/authorized']),
            _default_scopes='email',
            user=request.form.get('name')).save()
    clientkeys = Client.objects(user=session['email'])
    return render_template('service/oauth_gen.html', keys=clientkeys)

@service.route('/oauth_delete', methods=['POST'])
def oauth_delete():
    if request.method == 'POST':
        Client.objects(client_id=request.form.get('client_id')).delete()
        return redirect(url_for('service.oauth_gen'))

@service.route('/sensorgroup_delete', methods=['POST'])
def sensorgroup_delete():
    # cache process
    sensorgroup = SensorGroup.objects(name=request.form.get('name')).first()
    pipe = r.pipeline()

    for sensor_name in r.smembers('sensorgroup:{}'.format(sensorgroup.name)):
        pipe.srem('sensor:{}'.format(sensor_name), sensorgroup.name)

    # delete sensorgroup from the cache
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
    skip_size = (page - 1) * PAGE_SIZE
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


@service.route('/permission', methods=['GET', 'POST'])
def permission():
    page = request.args.get('page', 1, type=int)
    skip_size = (page - 1) * PAGE_SIZE
    objs = Permission.objects().skip(skip_size).limit(PAGE_SIZE)
    for obj in objs:
        obj.can_delete = True

    form = PermissionForm()
    form.user_group.choices = sorted([(obj.name, obj.name) for obj in UserGroup.objects])
    form.sensor_group.choices = sorted([(obj.name, obj.name) for obj in SensorGroup.objects])
    if form.validate_on_submit():
        # Doesn't allow duplicate permissions
        if Permission.objects(user_group=form.user_group.data, sensor_group=form.sensor_group.data).first() is not None:
            flash('There is already permission pair {} - {} specified'.format(
                form.user_group.data, form.sensor_group.data))
            return redirect(url_for('service.permission'))
        # If permission doesn't exist then create it
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
    """ Input taken from the user is their email and the sensor id they want to
        check the permission for. The result returned is what type of access
        permission the user has to that specific sensor """
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


@service.route('/sensor/search', methods=['GET', 'POST'])
def sensors_search():
    data = json.loads(request.args.get('q'))
    print data, type(data)
    args = {}
    for key, values in data.iteritems():
        if key == 'Building':
            args['building__in'] = values
        elif key == 'SourceName':
            args['source_name__in'] = values
        elif key == 'SourceIdentifier':
            args['source_identifier__in'] = values
        elif key == 'ID':
            args['name__in'] = values
        elif key == 'Tags':
            tag_list = []
            for tag in values:
                key_value = tag.split(":", 1)
                current_tag = {"name": key_value[0], "value": key_value[1]}
                tag_list.append(current_tag)
            args['tags_all'] = tag_list
        elif key == 'MetaData':
            metadata_list = []
            for meta in values:
                key_value = tag.split(":", 1)
                current_meta = {key_value[0]: key_value[1]}
                metdata_list.append(current_meta)
            args['metadata_all'] = metdata_list
    print args
    # Show the user PAGE_SIZE number of sensors on each page
    page = request.args.get('page', 1, type=int)
    skip_size = (page - 1) * PAGE_SIZE
    sensors = Sensor.objects(**args).skip(skip_size).limit(PAGE_SIZE)

    for sensor in sensors:
        sensor.can_delete = True

    total = len(Sensor.objects(**args))
    if (total):
        pages = int(math.ceil(float(total) / PAGE_SIZE))
    else:
        pages = 0
    form = SensorForm()
    # Get the list of valid buildings for this DataService
    form.building.choices = get_building_choices(current_app.config['NAME'])
    return render_template('service/sensor.html', objs=sensors, form=form, total=total,
                           pages=pages, current_page=page, pagesize=PAGE_SIZE)


@service.route('/graph/<name>')
@service.route('/sensor/graph/<name>')
def graph(name):
    objs = Sensor.objects()
    for obj in objs:
        if obj.name == name:
            temp = obj
            break
    metadata = Sensor._get_collection().find({'name': name}, {'metadata': 1, '_id': 0})[0]['metadata']
    metadata = [{'name': key, 'value': val} for key, val in metadata.iteritems()]
    obj = Sensor.objects(name=name).first()
    tags_owned = [{'name': tag.name, 'value': tag.value} for tag in obj.tags]
    return render_template('service/graph.html', name=name, obj=temp, metadata=metadata, tags=tags_owned)
