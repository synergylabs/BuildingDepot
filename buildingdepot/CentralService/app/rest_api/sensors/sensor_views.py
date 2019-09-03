"""
DataService.rest_api.sensor_views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying sensor models.
It handles the common services for sensors views, such as making a new one or
retrieving sensor view details. It manages the underlying cache, and will
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


class SensorViewService(MethodView):
    @check_oauth
    def get(self, name):
        """
        Retrieve sensor details based on uuid specified

        Args as data:
        name : <name of sensor>

        Returns (JSON):
        {
            'data':[{
                    'id' : <sensor uuid>,
                    'building' : <building name>
                    'tags' : <tags>,
                    }, {..}]
        }

        """
        if name is None:
            return jsonify(responses.missing_parameters)
        sensor = Sensor.objects(name=name).first()
        if sensor is None:
            return jsonify(responses.invalid_uuid)
        views_list = r.smembers('views:{}'.format(sensor.name))
        views = Sensor.objects(name__in=views_list)
        all_views = []
        for view in views:
            tags_owned = [{'name': tag.name, 'value': tag.value} for tag in view.tags]
            all_views.append({'building': str(view.building),
                             'id': str(view.name),
                             'tags': tags_owned
                             })
        response = dict(responses.success_true)
        response.update({"data": all_views})
        return jsonify(response)

    @check_oauth
    def post(self, name):
        """
        Creates sensor if the building specified is valid

        Args as data:
        "name":<name-of-view>
        "tags":<tags>

        Returns (JSON) :
        {
            "success": <True or False>
        }
        """
        if name is None:
            return jsonify(responses.missing_parameters)
        sensor = Sensor.objects(name=name).first()
        if sensor is None:
            return jsonify(responses.invalid_uuid)
        data = request.get_json()['data']
        try:
            view_name = data.get('name')
        except KeyError:
            return jsonify(responses.missing_parameters)

        identifier = data.get('identifier')
        uuid = data.get('uuid')
        email = get_email()
        building = sensor.building
        try:
            tags = data.get('tags')
            if not tags:
                tags = []
        except:
            tags = []
        for tag in tags:
            if tag['name'] == 'fields':
                fields = tag['value']
                break
            else:
                fields = ''
        tags = tags + [{"name": tag.name, "value": tag.value} for tag in sensor.tags] + [{"name": "parent", "value": sensor.name}]
        print tags
        if building in get_building_choices("rest_api"):
            if not uuid:
                uuid = str(uuid4())
            if defs.create_sensor(uuid, email, building):
                Sensor(name=uuid,
                       source_name=xstr(view_name),
                       source_identifier=xstr(identifier),
                       building=building,
                       owner=email,
                       tags=tags).save()
                r.set('owner:{}'.format(uuid), email)
                r.sadd('views:{}'.format(name), uuid)
                r.set('fields:{}'.format(uuid), fields)
                r.set('parent:{}'.format(uuid), name)
                r.sadd('views', uuid)
                response = dict(responses.success_true)
                response.update({'id': uuid})
                return jsonify(response)
            else:
                return jsonify(responses.ds_error)
        return jsonify(responses.invalid_building)

    @check_oauth
    def delete(self, name, uuid):
        if name is None:
            return jsonify(responses.missing_parameters)
        sensor = Sensor.objects(name=name).first()
        # cache process
        if get_email() == sensor.owner:
            if defs.delete_sensor(uuid):
                r.srem('views:{}'.format(sensor.name), uuid)
                r.delete('fields:{}'.format(uuid))
                r.delete('parent:{}'.format(uuid))
                r.delete(uuid)
                r.srem('views', uuid)
                # cache process done
                Sensor.objects(name=uuid).delete()
                response = dict(responses.success_true)
            else:
                response = dict(responses.ds_error)
        else:
            response = dict(responses.no_permission)
        return jsonify(response)
