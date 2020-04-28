"""
DataService.rest_api.sensorgroup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying sensor group models.
It handles the common services for sensor groups, such as making a new one
or deleting an existing one. Whenever a new group is created it caches a
list of the sensors that fall in this group. This list is further used
for acl's and other purposes.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""
from flask.views import MethodView
from flask import request,jsonify,current_app

from ...rpc import defs
from .. import responses
from ...models.cs_models import SensorGroup
from ... import r,oauth
from ..helper import xstr, get_building_choices, get_email, check_oauth
import sys

class SensorGroupService(MethodView):

    @check_oauth
    def post(self):
        """
        Args as data:
        name = <name of sensor group>
        description = <description for group>
        building = <building in which sensor group will be created>

        Returns (JSON) :
        {
            "success" : <True or False>
            "error" : <If False then error will be returned>
        }
        """
        try:
            data = request.get_json()['data']
            name = data['name']
            building = data['building']
            description = data['description']
        except KeyError:
            return jsonify(responses.missing_parameters)

        sensor_group = SensorGroup.objects(name=name).first()
        if sensor_group:
            return jsonify(responses.sensorgroup_exists)

        # Get the current user's email to assign as the owner for the sensor_group
        owner = get_email()

        # Get the list of buildings and verify that the one specified in the
        # request exists
        buildings_list = get_building_choices('rest_api')
        for item in buildings_list:
            if building in item:
                SensorGroup(name=xstr(name), building=xstr(building),
                            description=xstr(description), owner=xstr(owner)).save()
                return jsonify(responses.success_true)

        return jsonify(responses.invalid_building)

    @check_oauth
    def get(self):
        """
        Returns (JSON):
            {
                "result": [{
                    "success": <True or False>
                    "error": <If False then error will be returned>
                    "name": <name of sensor group>
                    "building": <building in which sensor group is located>
                    "description": <description attached to sensor group>
                }]
            }
        """
        sensor_groups = SensorGroup.objects(owner=get_email())
        result = []

        if sensor_groups is None:
            return jsonify(responses.invalid_sensorgroup)

        response = dict(responses.success_true)

        for sensor_group in sensor_groups:
            result.append({"name":sensor_group['name'], "building":sensor_group['building'], "description":sensor_group['description'], "tags":sensor_group['tags']})

        response.update({"result":result})
        return jsonify(response)

    @check_oauth
    def get(self,name):
        """
        Args as data:
            name = <name of sensor group>
        Returns (JSON):
            {
                "success" : <True or False>
                "error" : <If False then error will be returned
                "name" : <name of sensor group>
                "building" : <building in which sensor group is located>
                "description" : < description attached to sensor group"
            }
        """
        sensor_group = SensorGroup.objects(name=name).first()
        if sensor_group is None:
            return jsonify(responses.invalid_sensorgroup)

        response = dict(responses.success_true)
        response.update({"name":sensor_group['name'],
                        "building":sensor_group['building'],
                        "description":sensor_group['description']})
        return jsonify(response)

    @check_oauth
    def delete(self,name):
        """
        Args as data:
            name = <name of sensor group>
        Returns (JSON):
            {
                "success" : <True or False>
                "error" : <If False then error will be returned
            }
        """
        email = get_email()
        sensor_group = SensorGroup.objects(name=name).first()
        if sensor_group is None:
            return jsonify(responses.invalid_usergroup)
        if email == sensor_group.owner and defs.invalidate_permission(name):
            SensorGroup._get_collection().remove({"name":sensor_group['name']})
            response = dict(responses.success_true)
        else:
            response = dict(responses.sensorgroup_delete_authorization)
        return jsonify(response)
