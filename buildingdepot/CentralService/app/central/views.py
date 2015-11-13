from flask import render_template, request, redirect, url_for, jsonify
from . import central
from ..models.cs_models import *
from flask.ext.login import login_required
from app.common import PAGE_SIZE
from .forms import *
from .utils import get_choices, get_tag_descendant_pairs
from werkzeug.security import generate_password_hash


@central.route('/tagtype', methods=['GET', 'POST'])
@login_required
def tagtype():
    page = request.args.get('page', 1, type=int)
    skip_size = (page-1)*PAGE_SIZE
    objs = TagType.objects().skip(skip_size).limit(PAGE_SIZE)
    for obj in objs:
        if not obj.children and BuildingTemplate._get_collection().find({'tag_types': obj.name}).count() == 0:
            obj.can_delete = True
        else:
            obj.can_delete = False
    form = TagTypeForm()
    form.parents.choices = get_choices(TagType)
    if form.validate_on_submit():
        TagType(name=str(form.name.data),
                description=str(form.description.data),
                parents=form.parents.data).save()
        for parent in form.parents.data:
            collection = TagType._get_collection()
            collection.update(
                {'name': parent},
                {'$addToSet': {'children': str(form.name.data)}}
            )
        return redirect(url_for('central.tagtype'))
    return render_template('central/tagtype.html', objs=objs, form=form)


@central.route('/tagtype_delete', methods=['POST'])
@login_required
def tagtype_delete():
    name = request.form.get('name')
    TagType.objects(name=name).delete()
    collection = TagType._get_collection()
    collection.update(
        {'children': name},
        {'$pull': {'children': name}},
        multi=True
    )
    return redirect(url_for('central.tagtype'))


@central.route('/role', methods=['GET', 'POST'])
@login_required
def role():
    objs = Role.objects
    for obj in objs:
        if User.objects(role=obj).count() > 0:
            obj.can_delete = False
        else:
            obj.can_delete = True
    form = RoleForm()
    if form.validate_on_submit():
        Role(name=str(form.name.data),
             description=str(form.description.data),
             permission=form.permission.data,
             type=form.type.data).save()
        return redirect(url_for('central.role'))
    return render_template('central/role.html', objs=objs, form=form)


@central.route('/role_delete', methods=['POST'])
@login_required
def role_delete():
    name = request.form.get('name')
    Role.objects(name=name).delete()
    return redirect(url_for('central.role'))


@central.route('/buildingtemplate', methods=['GET', 'POST'])
@login_required
def buildingtemplate():
    page = request.args.get('page', 1, type=int)
    skip_size = (page-1)*PAGE_SIZE
    objs = BuildingTemplate.objects().skip(skip_size).limit(PAGE_SIZE)
    for obj in objs:
        if Building.objects(template=obj.name).count() > 0:
            obj.can_delete = False
        else:
            obj.can_delete = True
    form = BuildingTemplateForm()
    form.tag_types.choices = get_choices(TagType)
    if form.validate_on_submit():
        BuildingTemplate(name=str(form.name.data),
                         description=str(form.description.data),
                         tag_types=form.tag_types.data).save()
        return redirect(url_for('central.buildingtemplate'))
    return render_template('central/buildingtemplate.html', objs=objs, form=form)


@central.route('/buildingtemplate_delete', methods=['POST'])
@login_required
def buildingtemplate_delete():
    BuildingTemplate.objects(name=request.form.get('name')).delete()
    return redirect(url_for('central.buildingtemplate'))


@central.route('/building', methods=['GET', 'POST'])
@login_required
def building():
    page = request.args.get('page', 1, type=int)
    skip_size = (page-1)*PAGE_SIZE
    objs = Building.objects().skip(skip_size).limit(PAGE_SIZE)
    for obj in objs:
        if len(obj.tags) == 0:
            obj.can_delete = True
        else:
            obj.can_delete = False
    form = BuildingForm()
    form.template.choices = get_choices(BuildingTemplate)
    if form.validate_on_submit():
        Building(name=str(form.name.data),
                 description=str(form.description.data),
                 template=str(form.template.data)).save()
        return redirect(url_for('central.building'))
    return render_template('central/building.html', objs=objs, form=form)


@central.route('/building_delete', methods=['POST'])
@login_required
def building_delete():
    Building.objects(name=request.form.get('name')).delete()
    return redirect(url_for('central.building'))


@central.route('/building/<name>/metadata', methods=['GET', 'POST'])
@login_required
def building_metadata(name):
    if request.method == 'GET':
        metadata = Building._get_collection().find({'name': name}, {'metadata': 1, '_id': 0})[0]['metadata']
        metadata = [{'name': key, 'value': val} for key, val in metadata.iteritems()]
        return jsonify({'data': metadata})
    else:
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
    tag_name = request.form.get('tag_name')
    tag_value = request.form.get('tag_value')
    Building._get_collection().update(
        {'name': building_name},
        {'$pull': {'tags': {'name': tag_name, 'value': tag_value}}}
    )
    return redirect(url_for('central.building_tags', building_name=building_name))


@central.route('/building/<building_name>/tags/<tag_name>/<tag_value>/metadata', methods=['GET', 'POST'])
@login_required
def building_tags_metadata(building_name, tag_name, tag_value):
    if request.method == 'GET':
        metadata = Building._get_collection().aggregate([
            {'$unwind': '$tags'},
            {'$match': {'name': building_name, 'tags.name': tag_name, 'tags.value': tag_value}},
            {'$project': {'_id': 0, 'tags.metadata': 1}}
        ])['result'][0]['tags']['metadata']
        metadata = [{'name': key, 'value': val} for key, val in metadata.iteritems()]
        return jsonify({'data': metadata})
    else:
        metadata = {pair['name']: pair['value'] for pair in request.get_json()['data']}
        collection = Building._get_collection()
        tag = collection.aggregate([
            {'$unwind': '$tags'},
            {'$match': {'name': building_name, 'tags.name': tag_name, 'tags.value': tag_value}},
            {'$project': {'_id': 0, 'tags': 1}}
        ])['result'][0]['tags']
        tag['metadata'] = metadata
        collection.update(
            {'name': building_name},
            {'$pull': {'tags': {'name': tag_name, 'value': tag_value}}}
        )
        collection.update(
            {'name': building_name},
            {'$addToSet': {'tags': tag}}
        )
        return jsonify({'success': 'True'})


# ajax for adding a new tag for a building
@central.route('/building/<building_name>/add_tag', methods=['GET', 'POST'])
@login_required
def building_tags_ajax(building_name):
    if request.method == 'GET':
        template = Building.objects(name=building_name).first().template
        names = BuildingTemplate.objects(name=template).first().tag_types
        pairs = {name: TagType.objects(name=name).first().parents for name in names}
        tags = Building._get_collection().find(
            {'name': building_name},
            {'_id': 0, 'tags.name': 1, 'tags.value': 1, 'tags.parents': 1, 'tags.ancestors': 1}
        )[0]['tags']
        parents = set([pair['name']+pair['value'] for tag in tags for pair in tag['parents']])
        for tag in tags:
            tag['can_delete'] = tag['name']+tag['value'] not in parents
            tag['ancestors'] = [ancestor['name']+ancestor['value'] for ancestor in tag['ancestors']]
        return jsonify({'pairs': pairs, 'tags': tags, 'graph': get_tag_descendant_pairs()})
    else:
        data = request.get_json()['data']
        collection = Building._get_collection()
        ancestors = []
        if 'parents' in data:
            data['parents'] = [{'name': parent['name'], 'value': parent['value']} for parent in data['parents']]
            for parent in data['parents']:
                ancestors.extend(
                    collection.aggregate([
                        {'$unwind': '$tags'},
                        {'$match': {'name': building_name, 'tags.name': parent['name'], 'tags.value': parent['value']}},
                        {'$project': {'_id': 0, 'tags.ancestors': 1}}
                    ])['result'][0]['tags']['ancestors']
                )
            ancestors.extend(data['parents'])

        tag = {
            'name': data['name'],
            'value': data['value'],
            'metadata': {},
            'parents': [],
            'ancestors': ancestors
        }

        if 'parents' in data:
            tag['parents'] = data['parents']

        collection.update(
            {'name': building_name},
            {'$addToSet': {'tags': tag}}
        )
        return jsonify({'success': 'True'})



@central.route('/user', methods=['GET'])
@login_required
def user():
    return render_template('central/user.html')


@central.route('/user/add_user', methods=['GET', 'POST'])
@login_required
def user_ajax():
    if request.method == 'GET':
        objs = User.objects
        supers, locals, defaults = [], [], []
        for obj in objs:
            if obj.is_super():
                supers.append({'email': obj.email, 'name': obj.name})
            elif obj.is_local():
                locals.append({'email': obj.email, 'name': obj.name, 'buildings': obj.buildings})
            else:
                assigned_buildings = [item['building'] for item in obj.tags_owned]
                defaults.append({
                    'email': obj.email,
                    'name': obj.name,
                    'pairs':
                        [{'role': item.role, 'building': item.building, 'can_delete': item.building not in assigned_buildings} for item in obj.role_per_building],
                })
        emails = [super['email'] for super in supers] + \
                 [local['email'] for local in locals] + \
                 [default['email'] for default in defaults]
        buildings = [item['name'] for item in Building._get_collection().find({}, {'_id': 0, 'name': 1})]

        roles = [role.name for role in Role.objects if role.type == 'default' and role.name != 'default']

        return jsonify({'supers': supers, 'locals': locals, 'defaults': defaults,
                        'emails': emails, 'buildings': buildings, 'roles': roles})
    else:
        data = request.get_json()['data']
        User(email=data['email'],
             name=data['name'],
             password=generate_password_hash(data['password']),
             role=Role.objects(name=data['role']).first()).save()
        return jsonify({'success': 'True'})


@central.route('/user/<email>/add_managed_buildings', methods=['POST'])
@login_required
def user_add_managed_buildings(email):
    buildings = set(request.get_json()['data'])
    if '' in buildings:
        buildings.remove('')
    User.objects(email=email).update(set__buildings=buildings)
    return jsonify({'success': 'True'})


@central.route('/user/<email>/add_role_per_building', methods=['POST'])
@login_required
def user_add_role_per_building(email):
    pairs = request.get_json()['data']
    User.objects(email=email).update(set__role_per_building=pairs)
    User.objects(email=email).update(set__buildings=[item['building'] for item in pairs])
    return jsonify({'success': 'True'})


@central.route('/user/<email>/tags_owned', methods=['GET', 'POST'])
@login_required
def user_tags_owned(email):
    if request.method == 'GET':
        user = User.objects(email=email).first()
        buildings = user.buildings
        data = {}
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
        triples = [{'building': item.building,
                    'tags': [{'name': elem.name, 'value': elem.value} for elem in item.tags]}
                   for item in user.tags_owned]
        print triples, data
        return jsonify({'data': data, 'triples': triples})
    else:
        tags_owned = request.get_json()['data']
        print tags_owned
        User.objects(email=email).update(set__tags_owned=tags_owned)
        return jsonify({'success': 'True'})


@central.route('/dataservice', methods=['GET', 'POST'])
@login_required
def dataservice():
    objs = DataService.objects
    for obj in objs:
        obj.can_delete = True
    form = DataServiceForm()
    if form.validate_on_submit():
        DataService(name=str(form.name.data),
                    description=str(form.description.data),
                    host=str(form.host.data),
                    port=str(form.port.data)).save()
        return redirect(url_for('central.dataservice'))
    return render_template('central/dataservice.html', objs=objs, form=form)


@central.route('/dataservice/<name>/buildings', methods=['GET', 'POST'])
@login_required
def dataservice_buildings(name):
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
    if request.method == 'GET':
        admins = DataService._get_collection().find({'name': name}, {'admins': 1, '_id': 0})[0]['admins']
        user_emails = [user.email for user in User.objects]
        print user_emails
        return jsonify({'admins': admins, 'user_emails': user_emails})
    else:
        DataService.objects(name=name).update(set__admins=request.get_json()['data'])
        return jsonify({'success': 'True'})


@central.route('/dataservice_delete', methods=['POST'])
@login_required
def dataservice_delete():
    DataService.objects(name=request.form.get('name')).delete()
    return redirect(url_for('central.dataservice'))