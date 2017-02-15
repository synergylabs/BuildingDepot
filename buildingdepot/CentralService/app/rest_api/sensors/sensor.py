"""
DataService.rest_api.sensor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying sensor models.
It handles the common services for sensors, such as making a new one or
retrieving sensor details. It manages the underlying cache, and will
ensure that the cache gets updated as needed.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

import sys
from flask import request, jsonify
from flask.views import MethodView
from .. import responses
from ...models.cs_models import Sensor
from uuid import uuid4
from ... import r,oauth
from ..helper import get_email,xstr,get_building_choices
from ...auth.access_control import authenticate_acl
from ...rpc import defs

class SensorService(MethodView):

    @oauth.require_oauth()
    def get(self,name):
        """
        Retrieve sensor details based on uuid specified

        Args as data:
        name : <name of sensor>

        Returns (JSON):
        {
            'building': <name of building in which sensor is present>,
            'name' : <sensor uuid>,
            'tags' : tags_owned,
            'metadata' : metadata,
            'source_identifier' : str(sensor.source_identifier),
            'source_name' : str(sensor.source_name)
        }

        """
        if name is None:
            return jsonify(responses.missing_parameters)
        sensor = Sensor.objects(name=name).first()
        if sensor is None:
            return jsonify(responses.invalid_uuid)
        tags_owned = [{'name': tag.name, 'value': tag.value} for tag in sensor.tags]
        metadata = Sensor._get_collection().find({'name': name}, {'metadata': 1, '_id': 0})[0]['metadata']
        metadata = [{'name': key, 'value': val} for key, val in metadata.iteritems()]
        response = dict(responses.success_true)
        response.update({'building': str(sensor.building),
                        'name': str(sensor.name),
                        'tags': tags_owned,
			'Type': sensor.Enttype, #
                        'metadata': metadata,
                        'source_identifier': str(sensor.source_identifier),
                        'source_name': str(sensor.source_name)
                        })
        return jsonify(response)
    @oauth.require_oauth()
    def post(self):
        """
        Creates sensor if the building specified is valid

        Args as data:
        "name":<name-of-sensor>
        "building":<building in which sensor is present>
        "identifier":<identifier for sensor>

        Returns (JSON) :
        {
            "success": <True or False>
            "uuid" : <uuid of sensor if created>
            "error": <details of an error if it happends>
        }
        """
        data = request.get_json()['data']
        try:
            building = data['building']
	    sensorname = data['name'] #
        except KeyError:
            return jsonify(responses.missing_parameters)

      #  sensor_name = data.get('name') #
        identifier = data.get('identifier') 
        email = get_email()
	sensortype = "" #
	try:#
	    sensortype = data['type'] #
	except KeyError: #
		sensortype = "BasicBD" #
       # building = get_building_choices()[0]
#	print building
#	print get_building_choices("rest_api")
	if building in get_building_choices("rest_api"):
        	Extrauuid = str(uuid4()) #
		uuid = str(sensortype+":"+sensorname) #
        	if defs.create_sensor(uuid,email,building):
                   Sensor(name=uuid,
                       source_name=xstr(identifier),
                       source_identifier=xstr(identifier),
                       building=building,
                       owner=email,
		       Enttype = str(sensortype)).save() #
                   r.set('owner:{}'.format(uuid), email)
                   response = dict(responses.success_true)
                   response.update({'uuid':uuid})
                   return jsonify(response)
        	else:
                   return jsonify(responses.ds_error)
	return jsonify(responses.invalid_building)

