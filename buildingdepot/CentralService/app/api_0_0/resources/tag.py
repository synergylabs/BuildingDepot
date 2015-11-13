from flask.ext.restful import Resource, reqparse, fields, marshal
from utils import super_required, success, pagination_get
from ...models.cs_models import TagType, BuildingTemplate
from .. import auth
from ..errors import *

tag_type_fields = {
    'name': fields.String,
    'description': fields.String,
    'parents': fields.List(fields.String),
    'children': fields.List(fields.String)
}


class TagTypeAPI(Resource):
    decorators = [auth.login_required]

    def get(self, name):
        queried_obj = TagType.objects(name=name).first()
        if queried_obj is None:
            return not_exist('The queried tag type does not exist')
        return marshal(queried_obj, tag_type_fields)

    @super_required
    def delete(self, name):
        queried_obj = TagType.objects(name=name).first()
        if queried_obj is None:
            return not_exist('The queried tag type does not exist')
        if len(queried_obj.children) > 0:
            return not_allowed('Only tags with no children can be deleted')
        if BuildingTemplate._get_collection().find({'tag_types': 'room'}).count() > 0:
            return not_allowed('There is already buildingtemplate that references this tag type')
        TagType.objects(name=name).delete()
        collection = TagType._get_collection()
        collection.update(
            {'children': name},
            {'$pull': {'children': name}},
            multi=True
        )
        return success()


def tag_type_name_validator(name):
    if TagType.objects(name=name).count() > 0:
        raise ValueError('{} already exists'.format(name))
    return str(name)


def parents_validator(parents):
    if isinstance(parents, str) or isinstance(parents, unicode):
        if TagType.objects(name=parents).first() is None:
            raise ValueError('Parent tag {} does not exist'.format(parents))
        return [parents]
    if isinstance(parents, list):
        for parent in parents:
            if TagType.objects(name=parent).first() is None:
                raise ValueError('Parent tag {} does not exist'.format(parent))
        return parents
    raise ValueError('Parents tag must be string or list')


class TagTypeListAPI(Resource):
    decorators = [auth.login_required]

    def get(self):
        return pagination_get(TagType, tag_type_fields, TagTypeListAPI)

    @super_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=tag_type_name_validator, required=True, location='json')
        parser.add_argument('description', type=str, default='', location='json')
        parser.add_argument('parents', type=parents_validator, default=[], location='json')

        args = parser.parse_args()
        obj = TagType(name=args['name'], description=args['description'])
        if args['parents'] is not None:
            obj.parents = args['parents']
            collection = TagType._get_collection()
            for parent in args['parents']:
                collection.update(
                    {'name': parent},
                    {'$addToSet': {'children': args['name']}}
                )
        obj.save()
        return success()
