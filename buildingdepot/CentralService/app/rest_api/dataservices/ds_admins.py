"""
CentralService.rest_api.ds_admins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the interactions with the admins present in each
dataservice. It handles all the CRUD operations for the admins list
present in each dataservice.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask import jsonify, request
from flask.views import MethodView
from ...models.cs_models import Building, DataService, User
from .. import responses
from ... import oauth
from ...auth.access_control import super_required
from ..helper import check_oauth


class DataserviceAdminService(MethodView):
    @check_oauth
    @super_required
    def post(self, name):
        try:
            data = request.get_json()['data']
        except KeyError:
            return jsonify(responses.missing_data)

        admins = data.get('admins')
        if admins is None:
            return jsonify(responses.missing_parameters)

        dataservice = DataService.objects(name=name).first()
        if dataservice is None:
            return jsonify(responses.invalid_dataservice)

        for admin in admins:
            if User.objects(email=admin).first() is None:
                return jsonify(responses.ds_invalid_admin)

        dataservice.update(set__admins=admins)
        return jsonify(responses.success_true)

    @check_oauth
    def get(self, name):
        dataservice = DataService.objects(name=name).first()
        if dataservice is None:
            return jsonify(responses.invalid_dataservice)
        response = dict(responses.success_true)
        response.update({'admins': dataservice.admins})
        return jsonify(response)

    @check_oauth
    @super_required
    def delete(self, name):
        try:
            data = request.get_json()['data']
        except KeyError:
            return jsonify(responses.missing_data)

        dataservice = DataService.objects(name=name).first()
        if dataservice is None:
            return jsonify(responses.invalid_dataservice)

        admins = data.get('admins')
        if admins is None:
            return jsonify(responses.missing_parameters)

        collection = DataService._get_collection()
        collection.update({'name': name}, {'$pullAll': {'admins': admins}})
        return jsonify(responses.success_true)
