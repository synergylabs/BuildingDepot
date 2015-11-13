from flask import g, current_app
from flask.ext.restful import Api, Resource, reqparse, fields, marshal
from flask.ext.httpauth import HTTPBasicAuth
from ..models.cs_models import User
from errors import *

auth = HTTPBasicAuth()
api = Api(prefix='/api/v0.0')


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@auth.verify_password
def verify_auth(email_or_token, password):
    if email_or_token == '':
        return False
    if password == '':
        user = User.verify_auth_token(email_or_token)
        if user is not None:
            g.user = user
            g.token_used = True
            return True
        return False
    user = User.objects(email=email_or_token).first()
    if user is None:
        return False
    g.user = user
    g.token_used = False
    return True
    if user.verify_password(password):
        g.user = user
        g.token_used = False
        return True
    return False


class TokenAPI(Resource):
    decorators = [auth.login_required]

    def get(self):
        if g.token_used:
            return unauthorized('Invalid credentials')
        expires_in = current_app.config['TOKEN_EXPIRATION']
        return {'token': g.user.generate_auth_token(expires_in),
                'expires in': '{} minutes'.format(expires_in/60)}

api.add_resource(TokenAPI,
                 '/token', endpoint='token')

from resources.user import UserAPI, UserListAPI, UserLocalBuildingsAPI, \
    UserDefaultRolePerBuildingAPI, UserDefaultTagsOwnedAPI
api.add_resource(UserListAPI,
                 '/users', endpoint='users')
api.add_resource(UserAPI,
                 '/users/<string:email>', endpoint='user')
api.add_resource(UserLocalBuildingsAPI,
                 '/users/<string:email>/buildings', endpoint='user_local_buildings')
api.add_resource(UserDefaultRolePerBuildingAPI,
                 '/users/<string:email>/role_per_building', endpoint='user_default_role_per_building')
api.add_resource(UserDefaultTagsOwnedAPI,
                 '/users/<string:email>/tags_owned', endpoint='user_default_tags_owned')

from resources.tag import TagTypeAPI, TagTypeListAPI
api.add_resource(TagTypeListAPI,
                 '/tagtypes', endpoint='tagtypes')
api.add_resource(TagTypeAPI,
                 '/tagtypes/<string:name>', endpoint='tagtype')

from resources.building_template import BuildingTemplateAPI, BuildingTemplateListAPI, BuildingTemplateTagTypesAPI
api.add_resource(BuildingTemplateListAPI,
                 '/buildingtemplates', endpoint='buildingtemplates')
api.add_resource(BuildingTemplateAPI,
                 '/buildingtemplates/<string:name>', endpoint='buildingtemplate')
api.add_resource(BuildingTemplateTagTypesAPI,
                 '/buildingtemplates/<string:name>/tagtypes', endpoint='buildingtemplate_tagtypes')

from resources.building import BuildingAPI, BuildingListAPI, BuildingMetadataAPI, BuildingTagsAPI, \
    BuildingTagMetadataAPI
api.add_resource(BuildingAPI,
                 '/buildings/<string:name>', endpoint='building')
api.add_resource(BuildingMetadataAPI,
                 '/buildings/<string:name>/metadata', endpoint='building_metadata')
api.add_resource(BuildingListAPI,
                 '/buildings', endpoint='buildings')
api.add_resource(BuildingTagsAPI,
                 '/buildings/<string:name>/tags', endpoint='building_tags')
api.add_resource(BuildingTagMetadataAPI,
                 '/buildings/<string:building_name>/tags/<string:tag_name>/<string:value>/metadata',
                 endpoint='building_tag_metadata')

from resources.role import RoleAPI, RoleListAPI
api.add_resource(RoleListAPI,
                 '/roles', endpoint='roles')
api.add_resource(RoleAPI,
                 '/roles/<string:name>', endpoint='role')
