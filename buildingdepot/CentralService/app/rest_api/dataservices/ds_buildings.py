"""
CentralService.rest_api.ds_buildings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the interactions with the buildings present in each
dataservice. It handles all the CRUD operations for the buildings list
present in each dataservice.

@copyright: (c) 2024 SynergyLabs
@license: CMU License. See License file for details.
"""

from flask import jsonify, request
from flask.views import MethodView

from .. import responses
from ..helper import check_oauth
from ... import oauth
from ...auth.access_control import super_required
from ...models.cs_models import Building, DataService


class DataserviceBuildingsService(MethodView):
    @check_oauth
    @super_required
    def post(self, name):
        try:
            data = request.get_json()["data"]
        except KeyError:
            return jsonify(responses.missing_data)

        buildings = data.get("buildings")
        if buildings is None:
            return jsonify(responses.missing_parameters)

        dataservice = DataService.objects(name=name).first()
        if dataservice is None:
            return jsonify(responses.invalid_dataservice)

        for building in buildings:
            if Building.objects(name=building).first() is None:
                return jsonify(responses.ds_invalid_building)

        dataservice.update(add_to_set__buildings=buildings)
        return jsonify(responses.success_true)

    @check_oauth
    def get(self, name):
        dataservice = DataService.objects(name=name).first()
        if dataservice is None:
            return jsonify(responses.invalid_dataservice)
        response = dict(responses.success_true)
        response.update({"buildings": dataservice.buildings})
        return jsonify(response)

    @check_oauth
    @super_required
    def delete(self, name):
        try:
            data = request.get_json()["data"]
        except KeyError:
            return jsonify(responses.missing_data)

        dataservice = DataService.objects(name=name).first()
        if dataservice is None:
            return jsonify(responses.invalid_dataservice)

        buildings = data.get("buildings")
        if buildings is None:
            return jsonify(responses.missing_parameters)

        collection = DataService._get_collection()
        collection.update_one({"name": name}, {"$pullAll": {"buildings": buildings}})
        return jsonify(responses.success_true)
