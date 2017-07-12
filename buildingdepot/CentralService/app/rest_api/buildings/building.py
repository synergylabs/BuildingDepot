"""
CentralService.rest_api.building
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the interactions with the  buildings. Takes care
of all the CRUD operations on buildings. Each building can have values
defined for any of the tagtypes that the template it is based on contains.
Buildings can also have metadata attached to them.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask import jsonify, request
from flask.views import MethodView
from ...models.cs_models import Building, BuildingTemplate, DataService
from .. import responses
from ..helper import gen_update
from ... import oauth
from ...auth.access_control import super_required


class BuildingService(MethodView):
    params = ['name', 'template', 'description']

    @oauth.require_oauth()
    @super_required
    def post(self):
        try:
            data = request.get_json()['data']
        except KeyError:
            return jsonify(responses.missing_data)
        try:
            name = data['name']
            template = data['template']
        except KeyError:
            return jsonify(responses.missing_parameters)
        if BuildingTemplate.objects(name=template).first() is None:
            return jsonify(responses.invalid_template)
        building = Building.objects(name=name).first()
        if building is None:
            Building(**gen_update(self.params, data)).save()
        else:
            collection = Building._get_collection()
            collection.update({'name': name}, {"$set": gen_update(self.params, data)})
        return jsonify(responses.success_true)

    @oauth.require_oauth()
    def get(self, name):
        if name == 'list':
            building = []
            response = dict(responses.success_true)
            collection = Building.objects
            for i in collection:
                building.append(i.name)
            response.update({'buildings': building})
        else:
            building = Building.objects(name=name).first()
            if building is None:
                return jsonify(responses.invalid_building)
            response = dict(responses.success_true)
            response.update({'name': building['name'],
                             'description': building['description'],
                             'template': building['template']})
        return jsonify(response)

    @oauth.require_oauth()
    @super_required
    def delete(self, name):
        building = Building.objects(name=name).first()
        if building is None:
            return jsonify(responses.invalid_building)
        collection = DataService._get_collection()
        if len(building.tags) == 0 and collection.find({'buildings': name}).count() == 0:
            building.delete()
        else:
            return jsonify(responses.building_in_use)
        return jsonify(responses.success_true)
