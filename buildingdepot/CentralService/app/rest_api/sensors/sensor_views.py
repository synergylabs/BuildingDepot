"""
DataService.rest_api.sensor_views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying sensor models.
It handles the common services for sensors views, such as making a new one or
retrieving sensor view details. It manages the underlying cache, and will
ensure that the cache gets updated as needed.

@copyright: (c) 2020 SynergyLabs
@license: CMU License. See License file for details.
"""

from flask import request, jsonify
from flask.views import MethodView
from .. import responses
from ...models.cs_models import Sensor, Building
from uuid import uuid4
from ... import r, oauth
from ..helper import get_email, xstr, get_building_choices, check_oauth
from ...rpc import defs


class SensorViewService(MethodView):
    @check_oauth
    def get(self, name):
        """
        Retrieve sensor view details based on sensor uuid specified

        Args as data:
        name : <name of sensor>

        Returns (JSON):
        {
            'data':[{
                    'id' : <view uuid>,
                    'fields' : <view fields>
                    'source_name' : <view name>,
                    }, {..}]
        }

        """
        if name is None:
            return jsonify(responses.missing_parameters)
        sensor = Sensor.objects(name=name).first()
        if sensor is None:
            return jsonify(responses.invalid_uuid)
        views = Sensor.objects(tags__all=[{"name": "parent", "value": name}])
        available_fields = []
        for tag in sensor.tags:
            if tag['name'] == 'fields':
                available_fields += [field.strip() for field in tag['value'].split(",")]
        all_views = []
        for view in views:
            tags_owned = [{'name': tag.name, 'value': tag.value} for tag in view.tags]
            fields = []
            for tag in tags_owned:
                if tag['name'] == 'field':
                    fields.append(tag['value'])
            all_views.append({
                             'id': str(view.name),
                             'fields': ', '.join(sorted(fields)),
                             'source_name': xstr(view.source_name)
                             })
        response = dict(responses.success_true)
        response.update({"views_owned": all_views, 'available_fields': available_fields})
        return jsonify(response)

    @check_oauth
    def post(self, name):
        """
        Creates sensor view if the building and sensor specified are valid

        Args as data:
        "source_name":<name-of-view>
        "fields":<field1, field2...>

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
        if r.get('parent:{}'.format(name)):
            return jsonify({"success": "False", "error": "Sensor views can't have sub-views."})
        data = request.get_json()['data']
        try:
            view_name = data.get('source_name')
            fields = data.get('fields')
        except KeyError:
            return jsonify(responses.missing_parameters)

        email = get_email()
        building = sensor.building
        try:
            tags = data.get('tags')
            if not tags:
                tags = []
        except:
            tags = []
        fields_list = fields.split(',')
        field_tags = [{"name": "field", "value": field.strip()} for field in fields_list]
        available_tags = Building.objects(name=building).first().tags
        available_tags = [{"name": tag.name, "value": tag.value} for tag in available_tags]
        tags = tags + [{"name": tag.name, "value": tag.value} for tag in sensor.tags] + [{"name": "parent", "value": sensor.name}] + field_tags
        if any(tag not in available_tags for tag in tags):
            missing_tags = set([(tag['name'], tag['value']) for tag in tags]) - set([(tag['name'], tag['value']) for tag in available_tags])
            missing_tags = [{'name': name, 'value': value} for name, value in missing_tags]
            return jsonify({'success': 'False', 'building_tags_required': missing_tags, 'error': 'Cannot create '
                                                                                                 'sensor views '
                                                                                                 'without the '
                                                                                                 'required building '
                                                                                                 'tags.'})
        uuid = str(uuid4())
        if defs.create_sensor(uuid, email, building, fields, name):
            Sensor(name=uuid,
                   source_name=xstr(view_name),
                   source_identifier="SensorView",
                   building=building,
                   owner=email,
                   tags=tags).save()
            r.set('owner:{}'.format(uuid), email)
            r.sadd('views:{}'.format(name), uuid)
            r.set('fields:{}'.format(uuid), fields)
            r.set('parent:{}'.format(uuid), name)
            fields = [field.strip() for field in fields.split(",")]
            for field in fields:
                r.sadd('{}:{}'.format(name, field), uuid)
            r.sadd('views', uuid)
            response = dict(responses.success_true)
            response.update({'id': uuid})
            return jsonify(response)
        else:
            return jsonify(responses.ds_error)

    @check_oauth
    def delete(self, name, uuid):
        if name is None:
            return jsonify(responses.missing_parameters)
        sensor = Sensor.objects(name=name).first()
        # cache process
        if get_email() == sensor.owner:
            if defs.delete_sensor(uuid, name):
                fields = r.get('fields:{}'.format(uuid))
                if fields:
                    fields = fields.split(",")
                    fields = [field.strip() for field in fields]
                    for field in fields:
                        r.srem('{}:{}'.format(name, field), uuid)
                r.delete('fields:{}'.format(uuid))
                r.delete('parent:{}'.format(uuid))
                r.delete(uuid)
                r.srem('views', uuid)
                # cache process done
                Sensor.objects(name=uuid).delete()
                r.srem('views:{}'.format(sensor.name), uuid)
                response = dict(responses.success_true)
            else:
                response = dict(responses.ds_error)
        else:
            response = dict(responses.no_permission)
        return jsonify(response)
