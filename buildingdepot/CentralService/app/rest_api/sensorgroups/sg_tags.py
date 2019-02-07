"""
DataService.rest_api.sg_tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying sensor group models to
add and remove tags from them. Whenever tags are added or deleted from a group
it updates the cache where a list is maintained of the sensors that fall in each
group.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

import sys
from flask.views import MethodView
from flask import request,jsonify
from .. import responses
from ..helper import add_delete,get_building_tags, check_oauth
from ...models.cs_models import SensorGroup,Permission
from ... import r,oauth
from ...auth.access_control import authenticate_acl
from ...rpc import defs

class SensorGroupTagsService(MethodView):

    @check_oauth
    def get(self,name):
        """
        Args as data:
            "name" : <Name of SensorGroup>
        Returns (JSON):
            {
              "tags": {
                       "Tag Name": [ List of eligible values],
                       .
                       .
                       .
                      }, (These are the list of eligibile tags for this sensor)
              "tags_owned": [
                              {
                               "name": <Tag-Name>,
                               "value": <Tag-Value>
                              },
                              .
                              .
                              .
                            ] (These are the list of tags owned by this sensor)
            }
        """
        obj = SensorGroup.objects(name=name).first()
        if obj is None:
            return jsonify(responses.invalid_sensorgroup)
        tags_owned = [{'name': tag.name, 'value': tag.value} for tag in obj.tags]
        tags = get_building_tags(obj.building)
        response = dict(responses.success_true)
        response.update({'tags': tags, 'tags_owned': tags_owned})
        return jsonify(response)

    @check_oauth
    def post(self,name):
        """
        Args as data:
            "name" : <Name of SensorGroup>
        Following data in JSON:
            {
              "data": [
                       {
                        "name": <Tag-Name>,
                        "value": <Tag-Value>
                        },
                        .
                        .
                        .
                      ]
            }

            Returns:
            {
                "success" : <True or False>
            }
        """
        if Permission.objects(sensor_group=name).first() is not None:
            return jsonify(responses.sensorgroup_used)
        try:
            tags = request.get_json()['data']['tags']
        except KeyError:
            return jsonify(responses.missing_data)
        sensorgroup = SensorGroup.objects(name=name).first()
        if sensorgroup is None:
            return jsonify(responses.invalid_sensorgroup)
        validate_tags = self.check_tags(tags,sensorgroup.building)
        if validate_tags is not None:
            return validate_tags
        if defs.invalidate_permission(name):
            SensorGroup.objects(name=name).update(set__tags=tags)
        else:
            return jsonify(responses.ds_error)
        return jsonify(responses.success_true)

    def check_tags(self,tags,building):
        building_tags = get_building_tags(building)
        print building_tags
        print tags
        for tag in tags:
            tagtype = building_tags.get(tag.get('name'))
            print tagtype
            if tagtype is None:
                return jsonify(responses.invalid_tagtype)
            print tag.get('value')
            tag_values = tagtype.get('values')
            if tag.get('value') not in tag_values:
                return jsonify(responses.invalid_tag_value)
            if tagtype.get('acl_tag') is False:
                return jsonify(responses.invalid_tag_permission)
        return None



