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
from ..rest_api.helper import form_query
from uuid import uuid4
from .. import r, influx, permissions
import sys
import math

sys.path.append('/srv/buildingdepot')
from ..api_0_0.resources.utils import *
from ..api_0_0.resources.acl_cache import invalidate_permission


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
        r.set('owner:{}'.format(uuid), session['email'])
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
    pipe.delete('owner:{}'.format(request.form.get('name')))
    pipe.execute()
    # cache process done

    Sensor.objects(name=sensor.name).delete()
    return redirect(url_for('service.sensor'))


@service.route('/sensorgroup', methods=['GET', 'POST'])
def sensorgroup():
    page = request.args.get('page', 1, type=int)
    skip_size = (page - 1) * PAGE_SIZE
    objs = SensorGroup.objects().skip(skip_size).limit(PAGE_SIZE)
    for obj in objs:
        if Permission.objects(sensor_group=obj.name).count() > 0:
            obj.can_delete = False
        else:
            obj.can_delete = True

    form = SensorGroupForm()
    # Get list of valid buildings for this DataService and create a sensorgroup
    form.building.choices = get_building_choices(current_app.config['NAME'])
    if form.validate_on_submit():
        SensorGroup(name=str(form.name.data),
                    description=str(form.description.data),
                    building=str(form.building.data),
                    owner = session['email']).save()
        return redirect(url_for('service.sensorgroup'))
    return render_template('service/sensorgroup.html', objs=objs, form=form)


@service.route('/sensorgroup_delete', methods=['POST'])
def sensorgroup_delete():
    # cache process
    sensorgroup = SensorGroup.objects(name=request.form.get('name')).first()
    if sensorgroup['owner'] == session['email']:
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
    else:
        flash('You are not authorized to delete this sensor group')
    return redirect(url_for('service.sensorgroup'))


@service.route('/usergroup', methods=['GET', 'POST'])
def usergroup():
    page = request.args.get('page', 1, type=int)
    skip_size = (page - 1) * PAGE_SIZE
    objs = UserGroup.objects().skip(skip_size).limit(PAGE_SIZE)
    for obj in objs:
        if Permission.objects(user_group=obj.name).count() > 0:
            obj.can_delete = False
        else:
            obj.can_delete = True

    form = UserGroupForm()
    if form.validate_on_submit():
        UserGroup(name=str(form.name.data),
                  description=str(form.description.data),
                  owner = session['email']).save()
        return redirect(url_for('service.usergroup'))
    return render_template('service/usergroup.html', objs=objs, form=form)


@service.route('/usergroup_delete', methods=['POST'])
def usergroup_delete():
    # cahce process
    name = request.form.get('name')
    if authorize_addition(name,session['email']):
        users = UserGroup.objects(name=request.form.get('name')).first().users
        pipe = r.pipeline()
        for user in users:
            pipe.srem('user:{}'.format(user), name)
        pipe.execute()
        # cahce process done

        UserGroup.objects(name=name).delete()
    else:
        flash('You are not authorized to delete this user group')
    return redirect(url_for('service.usergroup'))


@service.route('/permission', methods=['GET', 'POST'], endpoint="permission")
def permission_create():
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
                   permission=str(form.permission.data),
                   owner = session['email']).save()
        invalidate_permission(str(form.sensor_group.data))
        r.hset('permission:{}:{}'.format(form.user_group.data,form.sensor_group.data),"permission",form.permission.data)
        r.hset('permission:{}:{}'.format(form.user_group.data,form.sensor_group.data),"owner",session['email'])
        return redirect(url_for('service.permission'))
    return render_template('service/permission.html', objs=objs, form=form)


@service.route('/permission_delete', methods=['POST'])
def permission_delete():
    code = request.form.get('name').split(':-:')
    permission = Permission.objects(user_group=code[0], sensor_group=code[1]).first()
    if permission['owner'] == session['email']:
        permission.delete()
        r.delete('permission:{}:{}'.format(code[0], code[1]))
        invalidate_permission(code[1])
    else:
        flash('You are not authorized to delete this permission')
    return redirect(url_for('service.permission'))


@service.route('/permission_query', methods=['GET', 'POST'])
def permission_query():
    """ Input taken from the user is their email and the sensor id they want to
        check the permission for. The result returned is what type of access
        permission the user has to that specific sensor """
    form = PermissionQueryForm()
    res = None
    if form.validate_on_submit():
        if not validate_users([form.user.data],True):
            flash('User {} does not exist'.format(form.user.data))
            return render_template('service/query.html', form=form, res=res)

        sensor = Sensor.objects(name=form.sensor.data).first()
        if sensor is None:
            flash('Sensor {} does not exist'.format(form.sensor.data))
            return render_template('service/query.html', form=form, res=res)

        res = permission(form.sensor.data, form.user.data)

    return render_template('service/query.html', form=form, res=res)


@service.route('/sensor/search', methods=['GET', 'POST'])
def sensors_search():
    data = json.loads(request.args.get('q'))
    print data, type(data)
    args = {}
    for key, values in data.iteritems():
        if key == 'Building':
            form_query('building',values,args,"$or")
        elif key == 'SourceName':
            form_query('source_name',values,args,"$or")
        elif key == 'SourceIdentifier':
            form_query('source_identifier',values,args,"$or")
        elif key == 'ID':
            form_query('name',values,args,"$or")
        elif key == 'Tags':
            form_query('tags',values,args,"$and")
        elif key == 'MetaData':
            form_query('metadata',values,args,"$and")
    print args
    # Show the user PAGE_SIZE number of sensors on each page
    page = request.args.get('page', 1, type=int)
    skip_size = (page - 1) * PAGE_SIZE
    collection = Sensor._get_collection().find(args)
    sensors = collection.skip(skip_size).limit(PAGE_SIZE)

    sensor_list = []
    for sensor in sensors:
        sensor = Sensor(**sensor)
        sensor.can_delete = True
        sensor_list.append(sensor)

    total = collection.count()
    if (total):
        pages = int(math.ceil(float(total) / PAGE_SIZE))
    else:
        pages = 0
    form = SensorForm()
    # Get the list of valid buildings for this DataService
    form.building.choices = get_building_choices(current_app.config['NAME'])
    return render_template('service/sensor.html', objs=sensor_list, form=form, total=total,
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
