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

import json
import requests
from app.common import PAGE_SIZE
from flask import render_template, request, redirect, url_for, jsonify, session, flash
from flask.ext.login import login_required
from werkzeug.security import generate_password_hash, gen_salt

from . import central
from .forms import *
from .utils import get_choices, get_tag_descendant_pairs
from ..models.cs_models import *
from ..oauth_bd.views import Client
from ..rest_api.helper import check_if_super


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
def oauth_delete():
    if request.method == 'POST':
        Client.objects(client_id=request.form.get('client_id')).delete()
        return redirect(url_for('central.oauth_gen'))
