"""
DataService.rest_api.usergroup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying user group models.
It handles the common services for user groups, such as making a new one
or deleting an existing one.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask.views import MethodView
from flask import request,jsonify
from ..models.ds_models import UserGroup
from ..service.utils import get_building_choices
from .. import r,oauth
from .helper import xstr,get_email
import sys

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
            return jsonify({'success': 'False', 'error': 'Missing parameters'})

        user_group = UserGroup.objects(name=name).first()
        if user_group:
            return jsonify({'success':'False','error':'Usergroup already exists'})

        UserGroup(name=xstr(name),
                  description=xstr(description),
                  owner = get_email()).save()
        return jsonify({'success': 'True'})

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
            return jsonify({"success":"False","error":"Usergroup doesn't exist"})

        return jsonify({"success":"True",
                        "name":user_group['name'],
                        "description":user_group['description']})