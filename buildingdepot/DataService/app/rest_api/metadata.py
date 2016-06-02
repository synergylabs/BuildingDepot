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
from ..models.ds_models import Sensor
from .. import oauth
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
        return jsonify({'data': metadata})

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
        metadata = {pair['name']: pair['value'] for pair in request.get_json()['data'] if pair['name'] != ''}
        sensor = Sensor.objects(name=name).first()
        sensor.update(set__metadata=metadata)
        return jsonify({'success': 'True'})

