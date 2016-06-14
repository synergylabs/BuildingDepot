from flask.ext.restful import Resource, reqparse, fields, marshal
from flask import request, g
from utils import super_required, success, pagination_get
from .. import auth
from ..errors import *

role_fields = {
    'name': fields.String,
    'description': fields.String,
    'permission': fields.Boolean,
    'type': fields.String,
}


class RoleAPI(Resource):
    decorators = [auth.login_required]

    def get(self, name):
        queried_obj = Role.objects(name=name).first()
        if queried_obj is None:
            return not_exist('The queried role does not exist')
        return marshal(queried_obj, role_fields)

    @super_required
    def delete(self, name):
        queried_obj = Role.objects(name=name).first()
        if queried_obj is None:
            return not_exist('The queried role does not exist')
        Role.objects(name=name).delete()
        return success()


def role_name_validator(name):
    if Role.objects(name=name).count() > 0:
        raise ValueError('Role {} already exists'.format(name))
    return str(name)


class RoleListAPI(Resource):
    decorators = [auth.login_required]

    @super_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=role_name_validator, required=True, location='json')
        parser.add_argument('description', type=str, default='', location='json')
        parser.add_argument('permission', type=bool, required=True, location='json')
        parser.add_argument('type', type=str, required=True, choices=['super', 'local', 'default'], location='json')

        args = parser.parse_args()
        Role(name=args['name'],
             description=args['description'],
             permission=args['permission'],
             type=args['type']).save()
        return success()

    def get(self):
        return pagination_get(Role, role_fields, RoleListAPI)