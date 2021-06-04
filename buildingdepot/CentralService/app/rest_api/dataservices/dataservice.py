"""
CentralService.rest_api.dataservice
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the interactions with the dataservice models. Takes care
of all the CRUD operations on dataservices. Each dataservice will have a list
of buildings and admins that belong to it.

@copyright: (c) 2021 SynergyLabs
@license: CMU License. See License file for details.
"""

from flask import request, jsonify
from flask.views import MethodView

from .. import responses
from ..helper import xstr, gen_update, check_oauth
from ... import oauth
from ...auth.access_control import super_required
from ...models.cs_models import DataService


class DataserviceService(MethodView):
    params = ["description", "host", "port"]

    @check_oauth
    @super_required
    def post(self):
        try:
            data = request.get_json()["data"]
        except KeyError:
            return jsonify(responses.missing_data)

        try:
            name = data["name"]
        except KeyError:
            return jsonify(responses.missing_parameters)

        if not name:
            return jsonify({"success": "False", "error": "Invalid Data Service name."})
        dataservice = DataService.objects(name=name).first()
        if dataservice is None:
            DataService(
                name=name,
                description=xstr(data.get("description")),
                host=str(data.get("host")),
                port=str(data.get("port")),
            ).save()
        else:
            collection = DataService._get_collection()
            collection.update({"name": name}, {"$set": gen_update(self.params, data)})
        return jsonify(responses.success_true)

    @check_oauth
    def get(self, name):
        print(("Name :", name))
        if name == "list":
            all_dataservices = []
            collection = DataService.objects
            for i in collection:
                all_dataservices.append(i.name)
            response = dict(responses.success_true)
            response.update({"dataservices": all_dataservices})
        else:
            dataservice = DataService.objects(name=name).first()
            if dataservice is None:
                return jsonify(responses.invalid_dataservice)
            response = dict(responses.success_true)
            response.update(
                {
                    "name": name,
                    "description": xstr(dataservice.description),
                    "host": xstr(dataservice.host),
                    "port": xstr(dataservice.port),
                }
            )
        return jsonify(response)

    @check_oauth
    @super_required
    def delete(self, name):
        dataservice = DataService.objects(name=name).first()
        if dataservice is None:
            return jsonify(responses.invalid_dataservice)
        if len(dataservice.buildings) > 0:
            return jsonify(responses.dataservice_in_use)
        dataservice.delete()
        return jsonify(responses.success_true)
