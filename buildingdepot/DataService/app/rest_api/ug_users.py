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
from flask.views import MethodView
from flask import request,jsonify
from . import responses
from ..models.ds_models import UserGroup
from ..service.utils import validate_users
from .helper import add_delete_users,get_email
from .. import r,oauth
import sys

sys.path.append('/srv/buildingdepot')
from ..api_0_0.resources.utils import authenticate_acl,authorize_addition
from ..api_0_0.resources.acl_cache import invalidate_user

class UserGroupUsersService(MethodView):

    @oauth.require_oauth()
    def get(self,name):
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
        response.update({'users':[{'user_id': user.user_id, 'manager': user.manager} for user in obj.users]})
        return jsonify(response)

    @oauth.require_oauth()
    def post(self,name):
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
            emails = request.get_json()['data']
        except:
            return jsonify(responses.missing_data)
        if UserGroup.objects(name=name).first() is None:
            return jsonify(responses.invalid_usergroup)
        if validate_users(emails):
            if authorize_addition(name,get_email()):
                # cache process
                user_group = UserGroup.objects(name=name).first()
                # Recalculate the list of users that have to be added and
                # removed from this group based on the new list received
                added, deleted = add_delete_users(user_group.users, emails)
                pipe = r.pipeline()
                for user in added:
                    pipe.sadd('user:{}'.format(user), user_group.name)
                    invalidate_user(name,user)
                for user in deleted:
                    pipe.srem('user:{}'.format(user), user_group.name)
                    invalidate_user(name,user)
                pipe.execute()
                # cache process done
                UserGroup.objects(name=name).update(set__users=emails)
                return jsonify(responses.success_true)
            else:
                return jsonify(responses.usergroup_add_authorization)
        return jsonify(responses.user_not_registered)

