"""
DataService.rest_api.permission
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying permission models.
It handles the required CRUD operations for permissions.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask.views import MethodView
from flask import request,jsonify
from ..models.ds_models import UserGroup,SensorGroup,Permission
from .. import r,oauth,permissions
import sys

sys.path.append('/srv/buildingdepot')
from ..api_0_0.resources.acl_cache import invalidate_permission

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
            return jsonify({'success': 'False', 'error': 'Missing parameters'})
        else:
            permission = Permission.objects(user_group=user_group, sensor_group=sensor_group).first()
            if permission is None:
                return jsonify({'success': 'False', 'error': 'Permission doesn\'t exist'})
            else:
                return jsonify({'success': 'True', 'permission': permission.permission})

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
        data = request.get_json()['data']
        try:
            sensor_group = data['sensor_group']
            user_group = data['user_group']
            permission = data['permission']
            print sensor_group,user_group,permission
        except KeyError:
            print data
            return jsonify({'success': 'False', 'error': 'Missing parameters'})

        if UserGroup.objects(name=user_group).first() is None:
            return jsonify({'success': 'False', 'error': 'User group doesn\'t exist'})
        if SensorGroup.objects(name=sensor_group).first() is None:
            return jsonify({'success': 'False', 'error': 'Sensor group doesn\'t exist'})
        if permissions.get(permission) is None:
            return jsonify({'success': 'False', 'error': 'Permission value doesn\'t exist'})

        curr_permission = Permission.objects(user_group=user_group, sensor_group=sensor_group).first()
        if curr_permission is not None:
            if get_email() == curr_permission['owner'] :
                Permission.objects(user_group=user_group,
                                   sensor_group=sensor_group).first().update(set__permission=permissions.get(permission))
            else:
                return jsonify({'success':'False','error':'You are not authorized to modify this permission'})
        else:
            Permission(user_group=user_group, sensor_group=sensor_group,
                       permission=permissions.get(permission),
                       owner=get_email()).save()
        invalidate_permission(sensor_group)
        r.hset('permission:{}:{}'.format(user_group, sensor_group),"permission",permissions.get(permission))
        r.hset('permission:{}:{}'.format(user_group, sensor_group),"owner",get_email())
        return jsonify({'success': 'True'})

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
            return jsonify({'success': 'False', 'error': 'Missing parameters'})
        else:
            permission = Permission.objects(user_group=user_group, sensor_group=sensor_group).first()
            if permission is None:
                return jsonify({'success': 'False', 'error': 'Permission is not defined'})
            else:
                if permission['owner'] == get_email():
                    permission.delete()
                    r.delete('permission:{}:{}'.format(user_group, sensor_group))
                    invalidate_permission(sensor_group)
                    return jsonify({'success': 'True'})
                else:
                    return jsonify({'success':'False','error': """You are not authorized
                        to delete this permisson"""})
