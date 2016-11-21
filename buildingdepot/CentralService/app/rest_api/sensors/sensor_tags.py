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
import sys
from flask.views import MethodView
from flask import request,jsonify
from ..import responses
from ...models.cs_models import Sensor,SensorGroup
from ..helper import get_building_tags
from ... import r,oauth
from ...rpc import defs
from ...auth.access_control import authenticate_acl

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
	    print "I happen"
            return jsonify(responses.invalid_uuid)
	tags_owned = [{'name': tag.name, 'value': tag.value} for tag in obj.tags]
        print len(tags_owned), "length"
	print tags_owned
	tags = get_building_tags(obj.building) #NEEDS TO BE CHANGED
        response = dict(responses.success_true)
        response.update({'tags': tags, 'tags_owned': tags_owned}) #NEEDS TO BE CHANGED
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
	print name
        NewTags = request.get_json()['data']
        print NewTags,type(NewTags)
	sensor = Sensor.objects(name=name).first()
	tags_owned = [{'name': tag.name, 'value': tag.value} for tag in sensor.tags]
	for tag in NewTags:
		tags_owned.append(tag)
        if defs.invalidate_sensor(name):
            if sensor is None:
                return jsonify(responses.invalid_uuid)
#	    NewList = []
#	    for key in tags.keys():
#		NewList.append(str(key)+":"+str(tags[key]))
            Sensor.objects(name=name).update(set__tags=tags_owned)
            r.delete(name)
        else:
            return jsonify(responses.ds_error)
        return jsonify(responses.success_true)
