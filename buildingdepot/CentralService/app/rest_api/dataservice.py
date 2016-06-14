"""
CentralService.rest_api.dataservice
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the interactions with the dataservice models. Takes care
of all the CRUD operations on dataservices. Each dataservice will have a list
of buildings and admins that belong to it.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask import request,jsonify
from flask.views import MethodView
from . import responses
from .helper import xstr,gen_update
from ..models.cs_models import DataService
from .. import oauth
from ..api_0_0.resources.utils import super_required

class DataserviceService(MethodView):

    params = ['description','host','port']

    @oauth.require_oauth()
    @super_required
    def post(self):
        try:
            data = request.get_json()['data']
        except KeyError:
            return jsonify(responses.missing_data)

        try:
            name = data['name']
        except KeyError:
            return jsonify(responses.missing_parameters)

        dataservice = DataService.objects(name=name).first()
        if dataservice is None:
            DataService(name=name,
                    description=xstr(data.get('description')),
                    host=str(data.get('host')),
                    port=str(data.get('port'))).save()
        else:
            collection = DataService._get_collection()
            collection.update({'name': name},{'$set':gen_update(self.params,data)})
        return jsonify(responses.success_true)

    @oauth.require_oauth()
    def get(self,name):
        dataservice = DataService.objects(name=name).first()
        if dataservice is None:
            return jsonify(responses.invalid_dataservice)
        response = dict(responses.success_true)
        response.update({'name':name,
            'description':xstr(dataservice.description),
            'host':xstr(dataservice.host),
            'port':xstr(dataservice.port)})
        return jsonify(response)

    @oauth.require_oauth()
    @super_required
    def delete(self,name):
        dataservice = DataService.objects(name=name).first()
        if dataservice is None:
            return jsonify(responses.invalid_dataservice)
        if len(dataservice.buildings) > 0:
            return jsonify(responses.dataservice_in_use)
        dataservice.delete()
        return jsonify(responses.success_true)