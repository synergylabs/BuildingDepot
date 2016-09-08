"""
DataService.rest_api.permission
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying permission models.
It handles the required CRUD operations for permissions.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""
import sys
from flask.views import MethodView
from ..helper import get_email
from .. import responses
from flask import request,jsonify
from ...models.cs_models import UserGroup,SensorGroup,Permission
from ... import r,oauth,permissions
from ...auth.acl_cache import invalidate_permission
from ...rpc import defs

class PermissionService(MethodView):

    @oauth.require_oauth()
    def get(self):
        """
        Args as data:
            user_group = <name of user group>
            sensor_group = <name of sensor group>
        Returns (JSON) :
            {
                "success" : <True or False>
                "permission" : <If True will return value of permission>",
                "error" : <If False then error will be returned>
            }
        """
        user_group = request.args.get('user_group')
        sensor_group = request.args.get('sensor_group')
        if not all([user_group, sensor_group]):
            return jsonify(responses.missing_parameters)
        else:
            permission = Permission.objects(user_group=user_group, sensor_group=sensor_group).first()
            if permission is None:
                return jsonify(responses.no_permission)
            else:
                response = dict(responses.success_true)
                response['permission'] = permission.permission
                return jsonify(response)

    @oauth.require_oauth()
    def post(self):
        """
        Args as data:
            "sensor_group": "name of sensor group"
            "user_group": "name of user group"
            "permisison": "value of permission"
        Returns (JSON) :
            {
                "success": <True or False>
                "error": <details of an error if unsuccessful>
            }
        """
        try:
            data = request.get_json()['data']
        except:
            return jsonify(responses.missing_data)
        try:
            sensor_group = data['sensor_group']
            user_group = data['user_group']
            permission = data['permission']
        except KeyError:
            return jsonify(responses.missing_parameters)

        if UserGroup.objects(name=user_group).first() is None:
            return jsonify(responses.no_usergroup)
        if SensorGroup.objects(name=sensor_group).first() is None:
            return jsonify(responses.no_sensorgroup)
        if permissions.get(permission) is None:
            return jsonify(responses.no_permission_val)

        email = get_email()
        if defs.create_permission(user_group,sensor_group,email,permissions.get(permission)):
            curr_permission = Permission.objects(user_group=user_group, sensor_group=sensor_group).first()
            if curr_permission is not None:
                if email == curr_permission['owner'] :
                    Permission.objects(user_group=user_group,
                                       sensor_group=sensor_group).first().update(set__permission=permissions.get(permission))
                else:
                    return jsonify(responses.permission_authorization)
            else:
                Permission(user_group=user_group, sensor_group=sensor_group,
                           permission=permissions.get(permission),
                           owner=email).save()
            invalidate_permission(sensor_group)
            r.hset('permission:{}:{}'.format(user_group, sensor_group),"permission",permissions.get(permission))
            r.hset('permission:{}:{}'.format(user_group, sensor_group),"owner",email)
        else:
            return jsonify(responses.ds_error)
        return jsonify(responses.success_true)

    @oauth.require_oauth()
    def delete(self):
        """
        Args as data:
            "user_group": "name of user group"
            "sensor_group": "name of sensor group"
        Returns (JSON):
            {
                "success": <True or False>
                "error": <details of an error if unsuccessful>
            }
        """
        user_group = request.args.get('user_group')
        sensor_group = request.args.get('sensor_group')
        if not all([user_group, sensor_group]):
            return jsonify(responses.missing_parameters)
        else:
            permission = Permission.objects(user_group=user_group, sensor_group=sensor_group).first()
            if permission is None:
                return jsonify(responses.permission_not_defined)
            else:
                if permission['owner'] == get_email():
                    if defs.delete_permission(user_group,sensor_group):
                        permission.delete()
                        r.delete('permission:{}:{}'.format(user_group, sensor_group))
                        invalidate_permission(sensor_group)
                    else:
                        return jsonify(responses.ds_error)
                    return jsonify(responses.success_true)
                else:
                    return jsonify(responses.permission_del_authorization)
