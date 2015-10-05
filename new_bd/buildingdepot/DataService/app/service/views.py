from flask import render_template, request, redirect, url_for, jsonify, flash
from . import service
from ..models.ds_models import *
from .forms import *
from .utils import *
from uuid import uuid4

from .. import r, influx


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


@service.route('/sensor/<name>/timeseries', methods=['POST'])
def sensor_timeseries(name):
    points = [[int(pair['time']), pair['value']] for pair in request.get_json()['data']]
    data = [{
        'name': name,
        'columns': ['time', 'value'],
        'points': points
    }]

    max_point = max(points)
    emails = r.smembers('subscribers:{}'.format(name))
    pipe = r.pipeline()
    for email in emails:
        pipe.set('latest_point:{}:{}'.format(name, email), '{}-{}'.format(max_point[0], max_point[1]))
    pipe.execute()

    influx.write_points(data)
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
                print res
                if res == 'r/w':
                    return render_template('service/query.html', form=form, res=res)
        if res == 'r':
            return render_template('service/query.html', form=form, res=res)

        sensor_tags = ['{}:{}'.format(tag.name, tag.value) for tag in sensor.tags]
        res = get_permission(sensor_tags, sensor.building, form.user.data)

    return render_template('service/query.html', form=form, res=res)