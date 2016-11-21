"""
CentalService.central.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains all the definitions for the CentralService frontend functions.
Any action on the Web interface will generate a call to one of these
functions that renders a html page.

For example opening up http://localhost:81/central/tagtype on your installation
of BD will call the tagtype() function

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

import json,requests,math
from app.common import PAGE_SIZE
from uuid import uuid4
from flask import render_template, request, redirect, url_for, jsonify, session, flash
from flask.ext.login import login_required
from werkzeug.security import generate_password_hash, gen_salt

from .. import r
from . import central
from .forms import *
from ..rpc import defs
from ..models.cs_models import *
from .utils import get_choices, get_tag_descendant_pairs
from ..oauth_bd.views import Client
from ..rest_api.helper import check_if_super,get_building_choices
from ..rest_api.helper import validate_users,form_query
from ..auth.access_control import authorize_addition,permission
from ..auth.acl_cache import invalidate_permission

@central.route('/tagtype', methods=['GET', 'POST'])
@login_required
def tagtype():
    """Returns the list of TagTypes currently present in the system and adds a new
       type if the form is submitted and succesfully validated"""
    page = request.args.get('page', 1, type=int)
    skip_size = (page - 1) * PAGE_SIZE
    objs = TagType.objects().skip(skip_size).limit(PAGE_SIZE)
    # Can be deleted only if no child has a dependency on it
    for obj in objs:
        if not obj.children and BuildingTemplate._get_collection().find({'tag_types': obj.name}).count() == 0:
            obj.can_delete = True
        else:
            obj.can_delete = False
    form = TagTypeForm()
    form.parents.choices = get_choices(TagType)
    if form.validate_on_submit():
        # Create the tag
        payload = {'data': {
            "name": str(form.name.data),
            "description": str(form.description.data),
            "parents": [str(parent) for parent in form.parents.data],
            "acl_tag": check_if_super(session['email'])
        }}
        res = requests.post(request.url_root + "api/tagtype", data=json.dumps(payload),
                            headers=session['headers']).json()
        if res['success'] == 'False':
            flash(res['error'])
        return redirect(url_for('central.tagtype'))
    return render_template('central/tagtype.html', objs=objs, form=form)


@central.route('/tagtype_delete', methods=['POST'])
@login_required
def tagtype_delete():
    """Deletes a tag"""
    name = request.form.get('name')
    res = requests.delete(request.url_root + "api/tagtype/" + name, headers=session['headers']).json()
    if res['success'] == 'False':
        flash(res['error'])
    return redirect(url_for('central.tagtype'))


@central.route('/buildingtemplate', methods=['GET', 'POST'])
@login_required
def buildingtemplate():
    """Create a buildingtemplate or retrieve the list of the current ones"""
    page = request.args.get('page', 1, type=int)
    skip_size = (page - 1) * PAGE_SIZE
    objs = BuildingTemplate.objects().skip(skip_size).limit(PAGE_SIZE)
    # If there are buildings using this template then mark as cannot be deleted
    for obj in objs:
        if Building.objects(template=obj.name).count() > 0:
            obj.can_delete = False
        else:
            obj.can_delete = True
        obj.tag_types = map(str, obj.tag_types)
    form = BuildingTemplateForm()
    # Get list of tags that this building can use
    form.tag_types.choices = get_choices(TagType)
    if form.validate_on_submit():
        payload = {'data': {
            "name": str(form.name.data),
            "description": str(form.description.data),
            "tag_types": form.tag_types.data
        }}
        res = requests.post(request.url_root + "api/template", data=json.dumps(payload),
                            headers=session['headers']).json()
        if res['success'] == 'False':
            flash(res['error'])
        return redirect(url_for('central.buildingtemplate'))
    return render_template('central/buildingtemplate.html', objs=objs, form=form)


@central.route('/buildingtemplate_delete', methods=['POST'])
@login_required
def buildingtemplate_delete():
    name = request.form.get('name')
    res = requests.delete(request.url_root + "api/template/" + name, headers=session['headers']).json()
    if res['success'] == 'False':
        flash(res['error'])
    return redirect(url_for('central.buildingtemplate'))


@central.route('/building', methods=['GET', 'POST'])
@login_required
def building():
    """Create a new building or retrive the list of buildings currently in
       the system"""
    page = request.args.get('page', 1, type=int)
    skip_size = (page - 1) * PAGE_SIZE
    objs = Building.objects().skip(skip_size).limit(PAGE_SIZE)
    # If the building doesn't have any tags associated to it then mark
    # it as can be deleted
    for obj in objs:
        if len(obj.tags) == 0:
            obj.can_delete = True
        else:
            obj.can_delete = False
    form = BuildingForm()
    form.template.choices = get_choices(BuildingTemplate)
    if form.validate_on_submit():
        # Create the building
        payload = {'data': {
            "name": str(form.name.data),
            "description": str(form.description.data),
            "template": form.template.data
        }}
        res = requests.post(request.url_root + "api/building", data=json.dumps(payload),
                            headers=session['headers']).json()
        if res['success'] == 'False':
            flash(res['error'])
        return redirect(url_for('central.building'))
    return render_template('central/building.html', objs=objs, form=form)


@central.route('/building_delete', methods=['POST'])
@login_required
def building_delete():
    name = request.form.get('name')
    res = requests.delete(request.url_root + "api/building/" + name, headers=session['headers']).json()
    if res['success'] == 'False':
        flash(res['error'])
    return redirect(url_for('central.building'))


# api
@central.route('/building/<name>/metadata', methods=['GET', 'POST'])
@login_required
def building_metadata(name):
    """If the request is a GET then retrieve the metadata associated with it. If it is a POST
       then update the metadata"""
    if request.method == 'GET':
        metadata = Building._get_collection().find({'name': name}, {'metadata': 1, '_id': 0})[0]['metadata']
        metadata = [{'name': key, 'value': val} for key, val in metadata.iteritems()]
        return jsonify({'data': metadata})
    else:
        # Update the metadata
        metadata = {pair['name']: pair['value'] for pair in request.get_json()['data']}
        Building.objects(name=name).update(set__metadata=metadata)
        return jsonify({'success': 'True'})


@central.route('/building/<building_name>/tags', methods=['GET'])
@login_required
def building_tags(building_name):
    return render_template('central/buildingtags.html', building_name=building_name)


@central.route('/building/<building_name>/tags_delete', methods=['POST'])
@login_required
def building_tags_delete(building_name):
    """Delete specific tags associated with the building"""
    data = {'data': {
        'name': request.form.get('tag_name'),
        'value': request.form.get('tag_value')
    }}
    res = requests.delete(request.url_root + "api/building/" + building_name + "/tags", data=json.dumps(data),
                          headers=session['headers']).json()
    if res['success'] == 'False':
        flash(res['error'])
    return redirect(url_for('central.building_tags', building_name=building_name))


@central.route('/user', methods=['GET'])
@login_required
def user():
    default = User.objects(role='default')
    super = User.objects(role='super')
    return render_template('central/user.html', super_user=super, default=default)


@central.route('/user/<email>/tags_owned', methods=['GET', 'POST'])
@login_required
def user_tags_owned(email):
    """Retrieve or update the list of tags associated with this user"""
    if request.method == 'GET':
        user = User.objects(email=email).first()
        buildings = user.buildings
        data = {}
        # Iterate over each building that this user is associated with and obtain the
        # building specific tags
        for building in buildings:
            tags = Building._get_collection().find(
                {'name': building}, {'tags.name': 1, 'tags.value': 1, '_id': 0})[0]['tags']
            sub = {}
            for tag in tags:
                if tag['name'] in sub:
                    sub[tag['name']].append(tag['value'])
                else:
                    sub[tag['name']] = [tag['value']]
            data[building] = sub
        # Form a list of dicts containing the building name and the tags which the user has for
        # that building
        triples = [{'building': item.building,
                    'tags': [{'name': elem.name, 'value': elem.value} for elem in item.tags]}
                   for item in user.tags_owned]
        print triples, data
        return jsonify({'data': data, 'triples': triples})
    else:
        tags_owned = request.get_json()['data']
        # Update the tags in MongoDB
        User.objects(email=email).update(set__tags_owned=tags_owned)
        return jsonify({'success': 'True'})


@central.route('/dataservice', methods=['GET', 'POST'])
@login_required
def dataservice():
    """Create a new DataService"""
    objs = DataService.objects
    for obj in objs:
        obj.can_delete = True
    form = DataServiceForm()
    if form.validate_on_submit():
        # Create the DataService
        payload = {'data': {
            "name": str(form.name.data),
            "description": str(form.description.data),
            "host": str(form.host.data),
            "port": str(form.port.data)
        }}
        res = requests.post(request.url_root + "api/dataservice", data=json.dumps(payload),
                            headers=session['headers']).json()
        if res['success'] == 'False':
            flash(res['error'])
        return redirect(url_for('central.dataservice'))
    return render_template('central/dataservice.html', objs=objs, form=form)


@central.route('/dataservice/<name>/buildings', methods=['GET', 'POST'])
@login_required
def dataservice_buildings(name):
    """Retreive or update the list of buildings that are attached to this DataService"""
    if request.method == 'GET':
        buildings = DataService._get_collection().find({'name': name}, {'buildings': 1, '_id': 0})[0]['buildings']
        building_names = [building.name for building in Building.objects]
        return jsonify({'buildings': buildings, 'building_names': building_names})
    else:
        DataService.objects(name=name).update(set__buildings=request.get_json()['data'])
        return jsonify({'success': 'True'})


@central.route('/dataservice/<name>/admins', methods=['GET', 'POST'])
@login_required
def dataservice_admins(name):
    """ Retrieve or update the list of admins for this DataService"""
    if request.method == 'GET':
        admins = DataService._get_collection().find({'name': name}, {'admins': 1, '_id': 0})[0]['admins']
        user_emails = [user.email for user in User.objects]
        return jsonify({'admins': admins, 'user_emails': user_emails})
    else:
        DataService.objects(name=name).update(set__admins=request.get_json()['data'])
        return jsonify({'success': 'True'})


@central.route('/dataservice_delete', methods=['POST'])
@login_required
def dataservice_delete():
    name = request.form.get('name')
    res = requests.delete(request.url_root + "api/dataservice/" + name, headers=session['headers']).json()
    if res['success'] == 'False':
        flash(res['error'])
    return redirect(url_for('central.dataservice'))


@central.route('/oauth_gen', methods=['GET', 'POST'])
@login_required
def oauth_gen():
    keys = []
    """If a post request is     made then generate a client id and secret key
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
    return render_template('central/oauth_gen.html', keys=clientkeys)


@central.route('/oauth_delete', methods=['POST'])
@login_required
def oauth_delete():
    if request.method == 'POST':
        Client.objects(client_id=request.form.get('client_id')).delete()
        return redirect(url_for('central.oauth_gen'))

@central.route('/sensor', methods=['GET', 'POST'])
@login_required
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
    form.building.choices = get_building_choices()
    # Create a Sensor
    if form.validate_on_submit():
        uuid = str(uuid4())
	if(form.sensor_name.data):
		if(form.sensor_type.data):
			uuid = str(form.sensor_type.data)+":"+str(form.sensor_name.data)
		else:
			uuid = "BasicBD:"+str(form.sensor_name.data)
	if (not form.sensor_type.data):
		thetype = "BasicBD"
	else:
		thetype = str(form.sensor_type.data)
        if defs.create_sensor(uuid,session['email'],form.building.data):
            Sensor(name=uuid,
                   source_name=str(form.source_name.data),
                   source_identifier=str(form.source_identifier.data),
                   building=str(form.building.data),
                   owner=session['email'],
		   Enttype=thetype).save()
            r.set('owner:{}'.format(uuid), session['email'])
            return redirect(url_for('central.sensor'))
        else:
            flash('Unable to communicate with the DataService')
    return render_template('central/sensor.html', objs=objs, form=form, total=total,
                           pages=pages, current_page=page, pagesize=PAGE_SIZE)


@central.route('/sensor_delete', methods=['POST'])
@login_required
def sensor_delete():
    sensor = Sensor.objects(name=request.form.get('name')).first()
    # cache process
    if defs.delete_sensor(request.form.get('name')):
        r.delete('sensor:{}'.format(sensor.name))
        r.delete('owner:{}'.format(sensor.name))
        # cache process done
        Sensor.objects(name=sensor.name).delete()
    else:
        flash('Unable to communicate with the DataService')
    return redirect(url_for('central.sensor'))

@central.route('/sensorgroup', methods=['GET', 'POST'])
@login_required
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
    form.building.choices = get_building_choices()
    print "Got building choices"
    if form.validate_on_submit():
        SensorGroup(name=str(form.name.data),
                    description=str(form.description.data),
                    building=str(form.building.data),
                    owner = session['email']).save()
        return redirect(url_for('central.sensorgroup'))
    return render_template('central/sensorgroup.html', objs=objs, form=form)

@central.route('/sensorgroup_delete', methods=['POST'])
@login_required
def sensorgroup_delete():
    # cache process
    sensorgroup = SensorGroup.objects(name=request.form.get('name')).first()
    if sensorgroup['owner'] == session['email']:
        if defs.invalidate_permission(request.form.get('name')):
            SensorGroup.objects(name=sensorgroup.name).delete()
        else:
            flash('Unable to communicate with the DataService')
    else:
        flash('You are not authorized to delete this sensor group')
    return redirect(url_for('central.sensorgroup'))

@central.route('/usergroup', methods=['GET', 'POST'])
@login_required
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
        return redirect(url_for('central.usergroup'))
    return render_template('central/usergroup.html', objs=objs, form=form)

@central.route('/usergroup_delete', methods=['POST'])
@login_required
def usergroup_delete():
    # cahce process
    name = request.form.get('name')
    if authorize_addition(name,session['email']):
        UserGroup.objects(name=name).delete()
    else:
        flash('You are not authorized to delete this user group')
    return redirect(url_for('central.usergroup'))

@central.route('/permission', methods=['GET', 'POST'], endpoint="permission")
@login_required
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
            return redirect(url_for('central.permission'))
        if defs.create_permission(form.user_group.data,form.sensor_group.data,session['email'],form.permission.data):
            # If permission doesn't exist then create it
            Permission(user_group=str(form.user_group.data),
                       sensor_group=str(form.sensor_group.data),
                       permission=str(form.permission.data),
                       owner = session['email']).save()
            invalidate_permission(str(form.sensor_group.data))
            r.hset('permission:{}:{}'.format(form.user_group.data,form.sensor_group.data),"permission",form.permission.data)
            r.hset('permission:{}:{}'.format(form.user_group.data,form.sensor_group.data),"owner",session['email'])
        else:
            flash('Unable to communicate with the DataService')
        return redirect(url_for('central.permission'))
    return render_template('central/permission.html', objs=objs, form=form)


@central.route('/permission_delete', methods=['POST'])
@login_required
def permission_delete():
    code = request.form.get('name').split(':-:')
    permission = Permission.objects(user_group=code[0], sensor_group=code[1]).first()
    if permission['owner'] == session['email']:
        if defs.delete_permission(code[0],code[1]):
            permission.delete()
            r.delete('permission:{}:{}'.format(code[0], code[1]))
            invalidate_permission(code[1])
        else:
            flash('Unable to communicate with the DataService')
    else:
        flash('You are not authorized to delete this permission')
    return redirect(url_for('central.permission'))

@central.route('/permission_query', methods=['GET', 'POST'])
@login_required
def permission_query():
    """ Input taken from the user is their email and the sensor id they want to
        check the permission for. The result returned is what type of access
        permission the user has to that specific sensor """
    form = PermissionQueryForm()
    res = None
    if form.validate_on_submit():
        if not validate_users([form.user.data],True):
            flash('User {} does not exist'.format(form.user.data))
            return render_template('central/query.html', form=form, res=res)

        sensor = Sensor.objects(name=form.sensor.data).first()
        if sensor is None:
            flash('Sensor {} does not exist'.format(form.sensor.data))
            return render_template('central/query.html', form=form, res=res)

        res = permission(form.sensor.data, form.user.data)

    return render_template('central/query.html', form=form, res=res)

@central.route('/sensor/search', methods=['GET', 'POST'])
@login_required
def sensors_search():
    	data = json.loads(request.args.get('q'))
        args = {}
	tempargs={}
        for key, values in data.iteritems():
	    Special = values[len(values)-1]
	    Special = Special[len(Special)-1:]
	    if Special in ['*', '+', '-']:
		newvalue = values[0]
		newvalue = [newvalue[:len(newvalue)-1]]
		if key == 'Type':
			form_query('Enttype', values, args, "$or")
			if Special == '*' or Special == '+':
				#Traverse Upwards
				loopvar = 1
				tempvalues = [values]
				newTemp = []
				while loopvar==1:
					loopvar = 0
					for singleValue in tempvalues:
						form_query("subClass", singleValue, tempargs,"$or")
						newCollect = BrickType._get_collection().find(tempargs)
						tempargs = []
						for newValue in newCollect:
							newName = newValue.get('name')
							form_query('Enttype', newName, args, "$or")
							newTemp.append(newName)
							loopvar = 1
						tempvalues = newTemp
						newTemp = []					
					
			if Special == '*' or Special =='-':
				#Traverse Downwards
				loopvar = 1
				tempvalues = [values]
				newTemp = []
				while loopvar==1:
					loopvar = 0
					for singleValue in tempvalues:
						form_query("superClass", singleValue, tempargs,"$or")
						newCollect = BrickType._get_collection().find(tempargs)
						tempargs = []
						for newValue in newCollect:
							newName = newValue.get('name')
							form_query('Enttype', newName, args, "$or")
							newTemp.append(newName)
							loopvar = 1
						tempvalues = newTemp
						newTemp = []			
			
		elif key =='Tags':
                        print "Point1"
                        print newvalue, "newvalue"
                        form_query('tags',newvalue,args,"$or")
                        loopvar = 1
                        tempvalues = [newvalue]
                        newTemp = tempvalues
                        Core = newvalue[0].split(':',1)[0]
			AntiRecursion = dict()
                        while loopvar==1:
                                print "Point2", tempvalues
                                loopvar = 0
				tempvalues = newTemp
				newTemp = []
                                for singleValue in tempvalues:
                                        print singleValue,"first"
					if singleValue[0] not in AntiRecursion:
						AntiRecursion[singleValue[0]] = 1
                                        	form_query('tags', singleValue, tempargs, "$or")
                                        	newCollect = Sensor._get_collection().find(tempargs)
                                        	tempargs = {}
                                        	for newValue in newCollect:
                                                	newName = newValue.get('name')
                                                	newTag = [Core+":"+newName]
                                                	print newTag,"second"
                                                	form_query('tags',newTag, args, "$or")
                                                	newTemp.append(newTag)
                                                	loopvar = 1

		else:
		  	return jsonify(responses.no_search_parameters) 
            elif key == 'Type':
		form_query('Enttype', values, args, "$or")
	    elif key == 'Building':
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
    #for key, values in data.iteritems():
     #   if key == 'Building':
      #      form_query('building',values,args,"$or")
      #  elif key == 'SourceName':
      #      form_query('source_name',values,args,"$or")
      #  elif key == 'SourceIdentifier':
      #      form_query('source_identifier',values,args,"$or")
      #  elif key == 'ID':
      #      form_query('name',values,args,"$or")
      #  elif key == 'Tags':
      #      form_query('tags',values,args,"$and")
     #   elif key == 'MetaData':
      #      form_query('metadata',values,args,"$and")
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
    	form.building.choices = get_building_choices()
    	return render_template('central/sensor.html', objs=sensor_list, form=form, total=total,
                           pages=pages, current_page=page, pagesize=PAGE_SIZE)

