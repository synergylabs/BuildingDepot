"""
DataService.rest_api.metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the interactions with the sensor metadata. Allows the
creation of new metadata that can be attached to the sensor and reading of
the metadata of a sensor specified by uuid.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask import request,jsonify
from flask.views import MethodView
from ...models.cs_models import Sensor
from ... import oauth
from .. import responses
import sys

class MetaDataService(MethodView):

    @oauth.require_oauth()
    def get(self,name):
        """
        Args as data:
            "name": <sensor-uuid>
        Returns (JSON):
            {
              "data": [
                       {
                          "name": <name of metadata>,
                          "value": <value of metadata>"
                       },
                       .
                       .
                       .

                      ]
            }

        For POST Request:
        Args as data:
        "name": <sensor uuid>

        Following data in JSON:
        {
          "data": [
                   {
                      "name": <name of metadata>,
                      "value": <value of metadata>"
                   },
                   .
                   .
                   .

                  ]
        }

        Returns (JSON):
        {
            "success": <True or false>
        }
        """
        metadata = Sensor._get_collection().find({'name': name}, {'metadata': 1, '_id': 0})[0]['metadata']
        metadata = [{'name': key, 'value': val} for key, val in metadata.iteritems()]
        response = dict(responses.success_true)
        response.update({'data': metadata})
        return jsonify(response)

    @oauth.require_oauth()
    def post(self,name):
        """
        Args as data:
            "name": <sensor uuid>
        Following data in JSON:
            {
              "data": [
                       {
                          "name": <name of metadata>,
                          "value": <value of metadata>"
                       },
                       .
                       .
                       .

                      ]
            }
        """
        try:
            data = request.get_json()['data']
        except KeyError:
            return jsonify(responses.missing_data)
        metadata = {pair['name']: pair['value'] for pair in data if pair['name'] != ''}
        sensor = Sensor.objects(name=name).first()
        if sensor is None:
            return jsonify(responses.invalid_uuid)
        sensor.update(set__metadata=metadata)
        return jsonify(responses.success_true)

