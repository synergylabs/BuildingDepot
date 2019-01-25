"""
DataService.rest_api.usergroup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying user group models.
It handles the common services for user groups, such as making a new one
or deleting an existing one.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""
import sys
from flask.views import MethodView
from flask import request,jsonify

from ...auth.access_control import authorize_addition
from .. import responses
from ...models.cs_models import UserGroup
from ... import r,oauth
from ..helper import xstr,get_email,get_building_choices

class UserGroupService(MethodView):

    @oauth.require_oauth()
    def post(self):
        """
        Args as data:
        name = <name of user group>
        description = <description for group>

        Returns (JSON) :
        {
            "success" : <True or False>
            "error" : <If False then error will be returned>
        }
        """
        try:
            data = request.get_json()
            name = data['name']
            description = data['description']
        except KeyError:
            return jsonify(responses.missing_parameters)

        user_group = UserGroup.objects(name=name).first()
        if user_group:
            return jsonify(responses.usergroup_exists)

        UserGroup(name=xstr(name),
                  description=xstr(description),
                  owner = get_email()).save()
        return jsonify(responses.success_true)

    @oauth.require_oauth()
    def get(self,name):
        """
        Args as data:
            name = <name of user group>
        Returns (JSON):
            {
                "success" : <True or False>
                "error" : <If False then error will be returned
                "name" : <name of user group>
                "description" : < description attached to user group>"
            }
        """
        user_group = UserGroup.objects(name=name).first()
        if user_group is None:
            return jsonify(responses.invalid_usergroup)

        response = dict(responses.success_true)
        response.update({"name":user_group['name'],
                        "description":user_group['description']})
        return jsonify(response)

    @oauth.require_oauth()
    def delete(self,name):
        """
        Args as data:
            name = <name of user group>
        Returns (JSON):
            {
                "success" : <True or False>
                "error" : <If False then error will be returned
            }
        """
        user_group = UserGroup.objects(name=name).first()
        if user_group is None:
            return jsonify(responses.invalid_usergroup)
        if authorize_addition(name, get_email()):
            UserGroup._get_collection().remove({"name":user_group['name']})
            response = dict(responses.success_true)
        else:
            response = dict(responses.usergroup_delete_authorization)
        return jsonify(response)

