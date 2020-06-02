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

from flask import request, jsonify
from flask.views import MethodView
from .. import responses
from ...models.cs_models import Sensor
from uuid import uuid4
from ... import r, oauth
from ..helper import get_email, xstr, get_building_choices, check_oauth
from ...rpc import defs


class SensorService(MethodView):
    @check_oauth
    def get(self, name):
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
        metadata = [{'name': key, 'value': val} for key, val in metadata.items()]
        response = dict(responses.success_true)
        response.update({'building': str(sensor.building),
                         'name': str(sensor.name),
                         'tags': tags_owned,
                         'metadata': metadata,
                         'source_identifier': str(sensor.source_identifier),
                         'source_name': str(sensor.source_name)
                         })
        return jsonify(response)

    @check_oauth
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
        except KeyError:
            return jsonify(responses.missing_parameters)

        sensor_name = data.get('name')
        identifier = data.get('identifier')
        uuid = data.get('uuid')
        email = get_email()
        fields = data.get('fields')
        try:
            tags = data.get('tags')
        except:
            tags = []

        if fields:
            if not tags:
                tags = []
            tags.append({"name": "fields", "value": fields})

        if building in get_building_choices("rest_api"):
            if not uuid:
                uuid = str(uuid4())
            if defs.create_sensor(uuid, email, building):
                Sensor(name=uuid,
                       source_name=xstr(sensor_name),
                       source_identifier=xstr(identifier),
                       building=building,
                       owner=email,
                       tags=tags).save()
                r.set('owner:{}'.format(uuid), email)
                response = dict(responses.success_true)
                response.update({'uuid': uuid})
                return jsonify(response)
            else:
                return jsonify(responses.ds_error)
        return jsonify(responses.invalid_building)

    @check_oauth
    def delete(self, name):
        if name is None:
            return jsonify(responses.missing_parameters)
        sensor = Sensor.objects(name=name).first()
        if r.get('parent:{}'.format(name)):
            return jsonify({'success': 'False', 'error': 'Sensor view can\'t be deleted.'})
        views = r.smembers('views:{}'.format(sensor.name))
        for view in views:
            if defs.delete_sensor(view):
                r.delete('sensor:{}'.format(view))
                r.delete('owner:{}'.format(view))
                # cache process done
                Sensor.objects(name=view).delete()
        # cache process
        if defs.delete_sensor(name):
            r.delete('sensor:{}'.format(sensor.name))
            r.delete('owner:{}'.format(sensor.name))
            # cache process done
            Sensor.objects(name=sensor.name).delete()
            response = dict(responses.success_true)
        else:
            response = dict(responses.ds_error)
        return jsonify(response)
