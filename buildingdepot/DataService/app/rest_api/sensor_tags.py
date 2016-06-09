"""
DataService.rest_api.sensor_tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the interactions with the sensor tags. Supports all
the CRUD operations on the tags of the sensor specified by the uuid. User
will have to have r/w/p permission to the sensor in order to be able to
update/remove tags from a sensor


@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""
from flask.views import MethodView
from flask import request,jsonify
from .import responses
from ..models.ds_models import Sensor,SensorGroup
from .helper import add_delete
from ..service.utils import get_building_tags
from .. import r,oauth

import sys
sys.path.append('/srv/buildingdepot')
from ..api_0_0.resources.utils import authenticate_acl

class SensorTagsService(MethodView):

    @oauth.require_oauth()
    def get(self,name):
        """
        Args as data:
        "name" : <sensor-uuid>

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
        } """
        obj = Sensor.objects(name=name).first()
        if obj is None:
            return jsonify(responses.invalid_uuid)
        tags_owned = [{'name': tag.name, 'value': tag.value} for tag in obj.tags]
        tags = get_building_tags(obj.building)
        response = dict(responses.success_true)
        response.update({'tags': tags, 'tags_owned': tags_owned})
        return jsonify(response)

    @oauth.require_oauth()
    @authenticate_acl('r/w/p')
    def post(self,name):
        """
        Args as data:
        "name" : <sensor-uuid>

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
            "success": <True or False>
        }
        """
        tags = request.get_json()['data']

        # cache process
        sensor = Sensor.objects(name=name).first()
        if sensor is None:
            return jsonify(responses.invalid_uuid)
        building = sensor.building
        # Get old tags and new tags and find the list of tags that have to be added and deleted
        # based on the response from get_add_delete
        old = ['tag:{}:{}:{}'.format(building, tag.name, tag.value) for tag in sensor.tags]
        new = ['tag:{}:{}:{}'.format(building, tag['name'], tag['value']) for tag in tags]
        added, deleted = add_delete(old, new)
        pipe = r.pipeline()
        for tag in added:
            pipe.sadd(tag, name)
        for tag in deleted:
            pipe.srem(tag, name)
        pipe.execute()

        # cache process done, update the values in MongoDB
        Sensor.objects(name=name).update(set__tags=tags)

        added = [tag.replace('tag', 'tag-sensorgroup', 1) for tag in added]
        deleted = [tag.replace('tag', 'tag-sensorgroup', 1) for tag in deleted]

        pipe = r.pipeline()
        # Also update in the cache the sensorgroups and tags that this specific sensor is attached to
        for key in added:
            for sensorgroup_name in r.smembers(key):
                sensorgroup = SensorGroup.objects(name=sensorgroup_name).first()
                sensorgroup_tags = {'tag:{}:{}:{}'.format(building, tag.name, tag.value) for tag in sensorgroup.tags}
                if sensorgroup_tags.issubset(new):
                    pipe.sadd('sensorgroup:{}'.format(sensorgroup_name), sensor.name)
                    pipe.sadd('sensor:{}'.format(sensor.name), sensorgroup_name)

        for key in deleted:
            for sensorgroup_name in r.smembers(key):
                pipe.srem('sensorgroup:{}'.format(sensorgroup_name), sensor.name)
                pipe.srem('sensor:{}'.format(sensor.name), sensorgroup_name)

        pipe.delete(sensor)
        pipe.execute()

        return jsonify(responses.success_true)
