from flask.ext.restful import Resource, reqparse, fields, marshal
from utils import super_required, success, pagination_get
from ...models.cs_models import BuildingTemplate, TagType
from .. import auth
from ..errors import *

building_template_fields = {
    'name': fields.String,
    'description': fields.String,
    'tag_types': fields.List(fields.String),
}


class BuildingTemplateAPI(Resource):
    decorators = [auth.login_required]

    def get(self, name):
        queried_obj = BuildingTemplate.objects(name=name).first()
        if queried_obj is None:
            return not_exist('The queried building template does not exist')
        return marshal(queried_obj, building_template_fields)

    @super_required
    def delete(self, name):
        queried_obj = BuildingTemplate.objects(name=name).first()
        if queried_obj is None:
            return not_exist('The queried building template does not exist')
        BuildingTemplate.objects(name=name).delete()
        return success()


def building_template_name_validator(name):
    if BuildingTemplate.objects(name=name).count() > 0:
        raise ValueError('Building template {} already exists'.format(name))
    return str(name)


def tag_types_validator(tag_types):
    if isinstance(tag_types, str) or isinstance(tag_types, unicode):
        if TagType.objects(name=tag_types).first() is None:
            raise ValueError('Tag type {} does not exist'.format(tag_types))
        return {tag_types}
    if isinstance(tag_types, list):
        tag_types = set(tag_types)
        for tag_type in tag_types:
            if TagType.objects(name=tag_type).first() is None:
                raise ValueError('Tag type {} does not exist'.format(tag_type))
        return tag_types
    raise ValueError('Tag types is neither string nor list')


class BuildingTemplateListAPI(Resource):
    decorators = [auth.login_required]

    def get(self):
        return pagination_get(BuildingTemplate, building_template_fields, BuildingTemplateListAPI)

    @super_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=building_template_name_validator, required=True, location='json')
        parser.add_argument('description', type=str, default='', location='json')
        parser.add_argument('tag_types', type=tag_types_validator, required=True, location='json')

        args = parser.parse_args()
        BuildingTemplate(name=args['name'], description=args['description'], tag_types=args['tag_types']).save()
        return success()


class BuildingTemplateTagTypesAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('tag_types', type=tag_types_validator, required=True, location='json')
        super(BuildingTemplateTagTypesAPI, self).__init__()

    @super_required
    def post(self, name):
        queried_obj = BuildingTemplate.objects(name=name).first()
        if queried_obj is None:
            return not_exist('The queried building template does not exist')
        updated = set(queried_obj.tag_types) | self.parser.parse_args()['tag_types']
        BuildingTemplate.objects(name=name).update_one(set__tag_types=updated)
        return success()

    @super_required
    def delete(self, name):
        queried_obj = BuildingTemplate.objects(name=name).first()
        if queried_obj is None:
            return not_exist('The queried building template does not exist')
        updated = set(queried_obj.tag_types) - self.parser.parse_args()['tag_types']
        BuildingTemplate.objects(name=name).update_one(set__tag_types=updated)
        return success()
