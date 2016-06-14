from flask import g, request
from copy import deepcopy
from flask.ext.restful import Resource, reqparse, fields, marshal
from werkzeug.security import generate_password_hash
from ...models.cs_models import User, Building
from .. import auth
from ..errors import *
from utils import *
from validate_email import validate_email


tags_owned_fields = {
    'tag': fields.String,
    'value': fields.String,
    'building': fields.String
}

super_user_fields = {
    'email': fields.String,
    'name': fields.String,
    'role': fields.String,
}

local_user_fields = deepcopy(super_user_fields).update({
    'buildings': fields.List(fields.String)
})

role_per_building_fields = {
    'role': fields.String,
    'building': fields.String
}

default_user_fields = deepcopy(super_user_fields).update({
    'role_per_building': fields.List(fields.Nested(role_per_building_fields)),
    'tags_owned': fields.List(fields.Nested(tags_owned_fields))
})


def user_api_get_res(user, fields_type):
    res = {
        'email': user.email,
        'name': user.name,
        'role': user.role.name,
    }
    if fields_type == 'super':
        return res
    if fields_type == 'local':
        res['buildings'] = user.buildings
        return res
    if fields_type == 'default':
        res['role_per_building'] = marshal(user.role_per_building, role_per_building_fields)
        res['tags_owned'] = marshal(user.tags_owned, tags_owned_fields)
        return res
    return internal_error('internal server error')


class UserAPI(Resource):
    decorators = [auth.login_required]

    def get(self, email):
        queried_user = User.objects(email=email).first()
        if queried_user is None:
            return not_exist('The queried user does not exist')

        def api_res():
            if is_super(queried_user):
                return user_api_get_res(queried_user, 'super')
            elif is_local(queried_user):
                return user_api_get_res(queried_user, 'local')
            elif is_default(queried_user):
                return user_api_get_res(queried_user, 'default')
            else:
                return internal_error('The queried user is dirty data')

        user = g.user
        if is_super(user):
            return api_res()

        if is_local(user):
            if is_managed_by_local(user, queried_user):
                return api_res()
            else:
                return not_allowed('The queried user is not affiliated with any one of your managed buildings')

        if is_default(user):
            if user.email == queried_user.email:
                return api_res()
            else:
                return not_allowed('You can only query your own user profile information')

        return internal_error('The queried user is dirty data')


def email_validator(email):
    if validate_email(email):
        if User.objects(email=email).count() > 0:
            raise ValueError('Email {} already exists'.format(email))
        else:
            return email
    else:
        raise ValueError('Email is not in valid format')


def password_validator(password):
    if len(password) <= 6:
        raise ValueError('Password length must be larger than 6')
    else:
        return password


def check_super_auth():
    authorization = request.authorization
    if authorization is None:
        return False
    email_or_token, password = authorization['username'], authorization['password']
    if email_or_token == '':
        return False
    if password == '':
        user = User.verify_auth_token(email_or_token)
        if user is None or user.role.type != 'super':
            return False
        return True
    user = User.objects(email=email_or_token).first()
    if user is None:
        return False
    # if user.role.type == 'super' and user.verify_password(password):
    if user.role.type == 'super':
        return True
    return False


def role_validator(name):
    role = Role.objects(name=name).first()
    if role is None:
        raise ValueError('Role {} does not exist'.format(name))
    if role.type in ['super', 'local']:
        if not check_super_auth():
            raise ValueError('Only super users can register a super role or local role user using API')
    return name


class UserListAPI(Resource):

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=email_validator, required=True, location='json')
        parser.add_argument('name', type=str, required=True, location='json', help='Name must not be empty')
        parser.add_argument('password', type=password_validator, required=True, location='json')
        parser.add_argument('role', type=role_validator, required=True, location='json')

        args = parser.parse_args()
        role = Role.objects(name=args['role']).first()
        User(email=args['email'],
             name=args['name'],
             password=generate_password_hash(args['password']),
             role=role).save()
        return success()


def building_exists(building_name):
    if Building.objects(name=building_name).first() is None:
        raise ValueError('Building {} does not exist'.format(building_name))


def buildings_validator(buildings):
    if isinstance(buildings, str) or isinstance(buildings, unicode):
        try:
            building_exists(buildings)
            return {buildings}
        except ValueError as e:
            raise e

    if isinstance(buildings, list):
        for building_name in buildings:
            try:
                building_exists(building_name)
                return set(buildings)
            except ValueError as e:
                raise e
    raise ValueError('Buildings must be string or list')


class UserLocalBuildingsAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('buildings', type=buildings_validator, required=True, location='json')
        super(UserLocalBuildingsAPI, self).__init__()

    @super_required
    def post(self, email):
        user = User.objects(email=email).first()
        if user is None:
            return not_exist('User {} does not exist'.format(email))
        if user.role.type != 'local':
            return not_allowed('You can only modify buildings for local role user')

        updated = set(user.buildings) | self.parser.parse_args()['buildings']
        User.objects(email=email).update_one(set__buildings=updated)
        return success()

    @super_required
    def delete(self, email):
        user = User.objects(email=email).first()
        if user is None:
            return not_exist('User {} does not exist'.format(email))
        if user.role.type != 'local':
            return not_allowed('You can only modify field buildings for local role user')

        updated = set(user.buildings) - self.parser.parse_args()['buildings']
        User.objects(email=email).update_one(set__buildings=updated)
        return success()


def check_role_building_pair(pair):
    """ validate input role_per_building pair

    1. Dict type
    2. Field role and building both exist
    3. Role does exist and must be default type
    4. Building does exist
    """
    if not isinstance(pair, dict):
        raise ValueError('Role building pair must be in dictionary type')
    if 'role' not in pair or 'building' not in pair:
        raise ValueError('Role building pair must contain both role and building')
    role = Role.objects(name=pair['role']).first()
    if role is None:
        raise ValueError('Role {} does not exist'.format(pair['role']))
    if role.type != 'default':
        raise ValueError('You can only assign role with default type')
    if Building.objects(name=pair['building']).first() is None:
        raise ValueError('Building {} does not exist'.format(pair['building']))


def role_per_building_validator(pairs):
    if isinstance(pairs, dict):
        try:
            check_role_building_pair(pairs)
        except ValueError as e:
            raise e
        return [pairs]
    elif isinstance(pairs, list):
        for pair in pairs:
            try:
                check_role_building_pair(pair)
            except ValueError as e:
                raise e

        # check whether the same building occurs more than once
        buildings = [elem['building'] for elem in pairs]
        if len(buildings) > len(set(buildings)):
            raise ValueError('A building cannot occur more than once in field role_per_building')
        return pairs
    raise ValueError('Field role_per_building must be in dictionary type or list type')


class UserDefaultRolePerBuildingAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('role_per_building', type=role_per_building_validator, required=True, location='json')
        super(UserDefaultRolePerBuildingAPI, self).__init__()

    @super_required
    def post(self, email):
        user = User.objects(email=email).first()
        if user is None:
            return not_exist('User {} does not exist'.format(email))
        if user.role.type != 'default':
            return not_allowed('You can only modify field role_per_building for default role user')

        # if building already exists in current role_per_building list, replace it with the new one

        def convert(arr):
            return {elem['building']: elem['role'] for elem in arr}

        pairs = convert(self.parser.parse_args()['role_per_building'])
        cur = convert(marshal(user.role_per_building, role_per_building_fields))
        print pairs, cur
        cur_key = cur.keys()
        for key in pairs.keys():
            if key in cur_key:
                del cur[key]
        pairs.update(cur)
        updated = [{'building': key, 'role': value} for key, value in pairs.iteritems()]
        User.objects(email=email).update_one(set__role_per_building=updated)
        User.objects(email=email).update_one(set__buildings=pairs.keys())
        return success()


from building import tag_exists


def check_tags_owned(pair):
    """ validate input tags_owned triplet

    1. Dict type
    2. Field building, tags all exist
    3. Building must be in the buildings list of the user
    4. The tag does exist in the building
    """
    if not isinstance(pair, dict):
        raise ValueError('The building tags pair be in dictionary type')
    if 'building' not in pair or 'tags' not in pair:
        raise ValueError('The pair must contain two fields: building and tags')
    if not isinstance(pair['tags'], list):
        raise ValueError('The tags field must be in list type')

    for item in pair['tags']:
        if not isinstance(item, dict):
            raise ValueError('The element inside tags must be in dict type')
        if 'name' not in item or 'value' not in item:
            raise ValueError('The element inside tags must contain two fields: name and value')

    buildings = User.objects(email=g.email).first().buildings
    if pair['building'] not in buildings:
        raise ValueError('{} is not a user of building {}'.format(g.email, pair['building']))

    for item in pair['tags']:
        if not tag_exists(pair['building'], item['name'], item['value']):
            raise ValueError('Tag {}-{} does not exist in building {}'
                             .format(pair['name'], item['value'], item['building']))


def tags_owned_validator(pairs):
    if isinstance(pairs, dict):
        try:
            check_tags_owned(pairs)
        except ValueError as e:
            raise e
        return [pairs]
    elif isinstance(pairs, list):
        for pair in pairs:
            try:
                check_tags_owned(pair)
            except ValueError as e:
                raise e

        # check whether the same  occurs more than once
        dup = set()
        for pair in pairs:
            for elem in pair['tags']:
                key = pair['building']+elem['name']+elem['value']
                if key in dup:
                    raise ValueError('The same building name value triplet occurs more than once')
                dup.add(key)
        return pairs
    raise ValueError('Field tags_owned must be in dictionary type or list type')


class UserDefaultTagsOwnedAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('tags_owned', type=tags_owned_validator, required=True, location='json')
        super(UserDefaultTagsOwnedAPI, self).__init__()

    @super_required
    def post(self, email):
        user = User.objects(email=email).first()
        if user is None:
            return not_exist('User {} does not exist'.format(email))
        if user.role.type != 'default':
            return not_allowed('You can only modify field tags_owned for default role user')
        g.email = email
        User.objects(email=email).update(set__tags_owned=self.parser.parse_args()['tags_owned'])
        return success()

        # User._get_collection().update(
        #     {'email': email},
        #     {'$addToSet': {'tags_owned': {'$each': self.parser.parse_args()['tags_owned']}}}
        # )