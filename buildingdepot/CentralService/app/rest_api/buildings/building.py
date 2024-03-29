"""
CentralService.rest_api.building
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the interactions with the  buildings. Takes care
of all the CRUD operations on buildings. Each building can have values
defined for any of the tagtypes that the template it is based on contains.
Buildings can also have metadata attached to them.

@copyright: (c) 2024 SynergyLabs
@license: CMU License. See License file for details.
"""

from flask import jsonify, request, current_app
from flask.views import MethodView

from .. import responses
from ..helper import gen_update, check_oauth
from ... import oauth
from ...auth.access_control import super_required
from ...models.cs_models import Building, BuildingTemplate, DataService


class BuildingService(MethodView):
    params = ["name", "template", "description"]

    @check_oauth
    @super_required
    def post(self):
        try:
            data = request.get_json()["data"]
        except KeyError:
            return jsonify(responses.missing_data)
        try:
            name = data["name"]
            template = data["template"]
        except KeyError:
            return jsonify(responses.missing_parameters)
        if BuildingTemplate.objects(name=template).first() is None:
            return jsonify(responses.invalid_template)
        if not name:
            return jsonify({"success": "False", "error": "Invalid Building name."})
        building = Building.objects(name=name).first()
        if building is None:
            Building(**gen_update(self.params, data)).save()
        else:
            collection = Building._get_collection()
            collection.update_one({"name": name}, {"$set": gen_update(self.params, data)})
        return jsonify(responses.success_true)

    @check_oauth
    def get(self, name):
        if name == "list":
            building = []
            response = dict(responses.success_true)
            collection = Building.objects
            for i in collection:
                building.append(i.name)
            response.update({"buildings": building})
        else:
            building = Building.objects(name=name).first()
            if building is None:
                return jsonify(responses.invalid_building)
            response = dict(responses.success_true)
            response.update(
                {
                    "name": building["name"],
                    "description": building["description"],
                    "template": building["template"],
                }
            )
        return jsonify(response)

    @check_oauth
    @super_required
    def delete(self, name):
        building = Building.objects(name=name).first()
        if building is None:
            return jsonify(responses.invalid_building)
        collection_objects = DataService.objects(buildings=name)
        if len(building.tags) == 0 and collection_objects.count() == 0:
            building.delete()
        else:
            return jsonify(responses.building_in_use)
        return jsonify(responses.success_true)
