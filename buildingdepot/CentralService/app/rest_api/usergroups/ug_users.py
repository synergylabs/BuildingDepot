"""
DataService.rest_api.ug_users
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying user group models to
add and remove users from them. Whenever users are added or deleted from a group
it updates the cache where a list is maintained of the users that fall in each
user group. This list is further used for acl's and other purposes.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""
import sys
from flask.views import MethodView
from flask import request, jsonify
from .. import responses
from ...models.cs_models import UserGroup
from ..helper import add_delete_users, get_email, validate_users, check_oauth
from ... import r, oauth
from ...auth.access_control import authenticate_acl, authorize_addition
from ...auth.acl_cache import invalidate_user


class UserGroupUsersService(MethodView):
    @check_oauth
    def get(self, name):
        """
        Args as data:
            name = <name of user group>
        Returns (JSON):
            {
                "users" : [user-id's,.......]
            }
        """
        obj = UserGroup.objects(name=name).first()
        if obj is None:
            return jsonify(responses.invalid_usergroup)
        response = dict(responses.success_true)
        response.update({
            'users': [{
                'user_id': user.user_id,
                'manager': user.manager
            } for user in obj.users]
        })
        return jsonify(response)

    @check_oauth
    def post(self, name):
        """
        Args as data:
            name = <name of user group>
            Following data as JSON:
            {
                "users" : [user-id's,.......]
            }
        Returns (JSON):
            {
                "success" : <True or False>
            }
        """
        try:
            emails = request.get_json()['data']['users']
        except:
            return jsonify(responses.missing_data)
        if UserGroup.objects(name=name).first() is None:
            return jsonify(responses.invalid_usergroup)
        if validate_users(emails):
            if authorize_addition(name, get_email()):
                user_group = UserGroup.objects(name=name).first()
                UserGroup.objects(name=name).update(set__users=emails)
                return jsonify(responses.success_true)
            else:
                return jsonify(responses.usergroup_add_authorization)
        return jsonify(responses.user_not_registered)
