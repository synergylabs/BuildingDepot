from flask.ext.restful import Resource, reqparse, fields, marshal
from flask import request, g
from utils import super_required, success, pagination_get
from ...models.cs_models import Building, BuildingTemplate, TagType
from .. import auth
from ..errors import *

node_fields = {
    'name': fields.String,
    'value': fields.String,
}

tags_fields = {
    'name': fields.String,
    'value': fields.String,
    'metadata': fields.Raw,
    'users': fields.List(fields.String),
    'parents': fields.List(fields.Nested(node_fields)),
    'ancestors': fields.List(fields.Nested(node_fields)),
}

building_fields = {
    'name': fields.String,
    'template': fields.String,
    'description': fields.String,
    'metadata': fields.Raw,
}


class BuildingAPI(Resource):
    decorators = [auth.login_required]

    def get(self, name):
        queried_obj = Building.objects(name=name).first()
        if queried_obj is None:
            return not_exist('The queried building does not exist')
        return marshal(queried_obj, building_fields)

    @super_required
    def delete(self, name):
        queried_obj = Building.objects(name=name).first()
        if queried_obj is None:
            return not_exist('The queried building template does not exist')
        Building.objects(name=name).delete()
        return success()


class BuildingMetadataAPI(Resource):
    decorators = [auth.login_required]

    def get(self, name):
        queried_obj = Building.objects(name=name).first()
        if queried_obj is None:
            return not_exist('The queried building does not exist')
        return queried_obj.metadata

    def post(self, name):
        queried_obj = Building.objects(name=name).first()
        if queried_obj is None:
            return not_exist('The queried building does not exist')

        parser = reqparse.RequestParser()
        parser.add_argument('metadata', type=dict, default={}, location='json')
        args = parser.parse_args()
        queried_obj.update(set__metadata=args['metadata'])
        return success()


def building_name_validator(name):
    if Building.objects(name=name).count() > 0:
        raise ValueError('Building {} already exists'.format(name))
    return str(name)


def template_validator(name):
    if BuildingTemplate.objects(name=name).first() is None:
        raise ValueError('Building template {} does not exist'.format(name))
    return str(name)


class BuildingListAPI(Resource):
    decorators = [auth.login_required]

    def get(self):
        return pagination_get(Building, building_fields, BuildingListAPI)

    @super_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=building_name_validator, required=True, location='json')
        parser.add_argument('template', type=template_validator, required=True, location='json')
        parser.add_argument('description', type=str, default='', location='json')
        parser.add_argument('metadata', type=dict, default={}, location='json')

        args = parser.parse_args()
        Building(name=args['name'],
                 template=args['template'],
                 description=args['description'],
                 metadata=args['metadata']).save()
        return success()


def tag_exists(building_name, tag_type, value):
    collection = Building._get_collection()
    cnt = collection.find(
        {
            'name': building_name,
            'tags': {
                '$elemMatch': {
                    'name': tag_type,
                    'value': str(value)
                }
            }
        }
    ).count()
    if cnt == 0:
        return False
    return True


def tag_name_validator(name):
    if TagType.objects(name=name).first() is None:
        raise ValueError('Tag type {} does not exist'.format(name))
    return str(name)


def tag_value_validator(value):
    if tag_exists(g.name, request.json['name'], value):
        raise ValueError('Tag {}-{} already exists'.format(request.json['name'], value))
    return str(value)


def check_parent_tag(parent_tag, child_name):
    """ check whether a prent tag is valid

    1. check whether parent is a dict and contains both name and value
    2. check whether the parent tag can truly the the parent of the child in TagType
    3. check whether the parent tag exists in the tags field of the building
    """

    if not isinstance(parent_tag, dict):
        raise ValueError('Parent tag must be in dictionary type')
    if 'name' not in parent_tag or 'value' not in parent_tag:
        raise ValueError('Parent tag must contain both name and value')

    tag_type = TagType.objects(name=parent_tag['name']).first()
    if tag_type is None:
        raise ValueError('Parent tag type {} does not exist'.format(parent_tag['name']))
    if child_name not in tag_type.children:
        raise ValueError('Tag type {} cannot be the parent of {}'.format(parent_tag['name'], child_name))

    if not tag_exists(g.name, parent_tag['name'], parent_tag['value']):
        raise ValueError('Parent tag {}-{} does not exist in building {}'.format(
            parent_tag['name'], parent_tag['value'], g.name))


def parents_tag_validator(parents):
    if isinstance(parents, dict):
        try:
            check_parent_tag(parents, request.json['name'])
        except ValueError as e:
            raise e
        return [parents]
    elif isinstance(parents, list):
        for parent in parents:
            try:
                check_parent_tag(parent, request.json['name'])
            except ValueError as e:
                raise e
        return parents
    raise ValueError('Field parents must be in dictionary type or list type')


class BuildingTagsAPI(Resource):
    decorators = [auth.login_required]

    @super_required
    def post(self, name):
        """ post a new tag for a building

        Also append the ancestors of the parent tag to the ancestors field of the child tag
        The ancestors field should also include parent tag
        """

        queried_obj = Building.objects(name=name).first()
        if queried_obj is None:
            return not_exist('The queried building does not exist')

        parser = reqparse.RequestParser()
        parser.add_argument('name', type=tag_name_validator, required=True, location='json')
        parser.add_argument('value', type=tag_value_validator, required=True, location='json')
        parser.add_argument('metadata', type=dict, default={}, location='json')
        parser.add_argument('parents', type=parents_tag_validator, default=[], location='json')

        g.name = name
        args = parser.parse_args()
        collection = Building._get_collection()

        ancestors = []
        for parent in args['parents']:
            ancestors.extend(
                collection.aggregate([
                    {'$unwind': '$tags'},
                    {'$match': {'name': name, 'tags.name': parent['name'], 'tags.value': str(parent['value'])}},
                    {'$project': {'_id': 0, 'tags.ancestors': 1}}
                ])['result'][0]['tags']['ancestors']
            )
        ancestors.extend(args['parents'])

        tag = {
            'name': args['name'],
            'value': args['value'],
            'metadata': args['metadata'],
            'parents': args['parents'],
            'ancestors': ancestors
        }
        collection.update(
            {'name': name},
            {'$addToSet': {'tags': tag}}
        )
        return success()

    def get(self, name):
        queried_obj = Building.objects(name=name).first()
        if queried_obj is None:
            return not_exist('The queried building does not exist')

        parser = reqparse.RequestParser()
        from utils import page_validator
        from app.common import PAGE_SIZE
        from ... import api
        parser.add_argument('page', type=page_validator, default=1, location='args')
        page = parser.parse_args()['page']
        skip_size = (page-1) * PAGE_SIZE
        tags = queried_obj.tags
        cnt = len(tags)

        res = {'data': []}
        if skip_size < cnt:
            tags = tags[skip_size: skip_size+PAGE_SIZE]
            res['data'] = [marshal(tag, tags_fields) for tag in tags]
        if page > 1:
            res['prev'] = api.url_for(BuildingTagsAPI, _external=True, page=page-1)
        if skip_size + PAGE_SIZE < cnt:
            res['next'] = api.url_for(BuildingTagsAPI, _external=True, page=page+1)
        return res


class BuildingTagMetadataAPI(Resource):
    decorators = [auth.login_required]

    def get(self, building_name, tag_name, value):
        if not tag_exists(building_name, tag_name, value):
            return not_exist('Tag {}-{} does not exist in building {}'.format(building_name, tag_name, value))

        return Building._get_collection().aggregate([
            {'$unwind': '$tags'},
            {'$match': {'name': building_name, 'tags.name': tag_name, 'tags.value': value}},
            {'$project': {'_id': 0, 'tags': 1}}
        ])['result'][0]['tags']['metadata']

    @super_required
    def post(self, building_name, tag_name, value):
        if not tag_exists(building_name, tag_name, value):
            return not_exist('Tag {}-{} does not exist in building {}'.format(building_name, tag_name, value))

        parser = reqparse.RequestParser()
        parser.add_argument('metadata', type=dict, default={}, location='json')
        args = parser.parse_args()

        collection = Building._get_collection()
        tag = collection.aggregate([
            {'$unwind': '$tags'},
            {'$match': {'name': building_name, 'tags.name': tag_name, 'tags.value': value}},
            {'$project': {'_id': 0, 'tags': 1}}
        ])['result'][0]['tags']
        tag['metadata'] = args['metadata']

        collection.update(
            {'name': building_name},
            {'$pull': {'tags': {'name': tag_name, 'value': value}}}
        )
        collection.update(
            {'name': building_name},
            {'$addToSet': {'tags': tag}}
        )
        return success()
