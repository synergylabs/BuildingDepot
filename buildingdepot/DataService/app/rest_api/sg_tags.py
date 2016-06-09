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
from flask.views import MethodView
from flask import request,jsonify
from . import responses
from .helper import add_delete
from ..models.ds_models import SensorGroup,Permission
from ..service.utils import get_building_tags
from .. import r,oauth
import sys

sys.path.append('/srv/buildingdepot')
from utils import get_user_oauth
from ..api_0_0.resources.utils import authenticate_acl

class SensorGroupTagsService(MethodView):

    @oauth.require_oauth()
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

    @oauth.require_oauth()
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
            tags = request.get_json()['data']
        except KeyError:
            return jsonify(responses.missing_data)
        # cache process
        sensorgroup = SensorGroup.objects(name=name).first()
        if sensorgroup is None:
            return jsonify(responses.invalid_sensorgroup)
        old = ['tag-sensorgroup:{}:{}:{}'.format(sensorgroup.building, tag.name, tag.value) for tag in sensorgroup.tags]
        new = ['tag-sensorgroup:{}:{}:{}'.format(sensorgroup.building, tag['name'], tag['value']) for tag in tags]
        added, deleted = add_delete(old, new)
        pipe = r.pipeline()
        for tag in added:
            pipe.sadd(tag, name)
        for tag in deleted:
            pipe.srem(tag, name)
        pipe.set('tag-count:{}'.format(name), len(new))
        # recalculate the sensors that this sensorgroup contains
        tags_owned = ['tag:{}:{}:{}'.format(sensorgroup.building, tag['name'], tag['value']) for tag in tags]

        old_sensors = r.smembers('sensorgroup:{}'.format(name))
        new_sensors = r.sinter(tags_owned) if len(tags_owned) > 0 else []
        added, deleted = add_delete(old_sensors, new_sensors)

        for sensor_name in added:
            pipe.sadd('sensor:{}'.format(sensor_name), name)
            pipe.delete(sensor_name)
        for sensor_name in deleted:
            pipe.srem('sensor:{}'.format(sensor_name), name)
            pipe.delete(sensor_name)

        r.delete('sensorgroup:{}'.format(name))
        for item in new_sensors:
            pipe.sadd('sensorgroup:{}'.format(name), item)
        pipe.execute()
        # cache process done
        SensorGroup.objects(name=name).update(set__tags=tags)
        return jsonify(responses.success_true)

