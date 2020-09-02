"""
DataService.rest_api.search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the search functionality, enabling users to
search for Sensors based on a combination of the parameters that
a sensor contains such as Tags,Building,Source identifier,uuid etc.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask import request, jsonify
from flask.views import MethodView
from .. import responses
from ...models.cs_models import Sensor
from ..helper import form_query, create_response, check_oauth
from ... import oauth


class SearchService(MethodView):
    @check_oauth
    def post(self):
        try:
            data = request.get_json()['data']
        except KeyError:
            return jsonify(responses.missing_data)

        args = {}
        for key, values in data.iteritems():
            if key == 'Building':
                form_query('building', values, args, "$and")
            elif key == 'SourceName':
                form_query('source_name', values, args, "$and")
            elif key == 'SourceIdentifier':
                form_query('source_identifier', values, args, "$and")
            elif key == 'Owner':
                form_query('owner', values, args, "$and")
            elif key == 'ID':
                form_query('name', values, args, "$and")
            elif key == 'Tags':
                form_query('tags', values, args, "$and")
            elif key == 'MetaData':
                form_query('metadata', values, args, "$and")
        if not args:
            return jsonify(responses.no_search_parameters)
        collection = Sensor._get_collection().find(args)

        response = dict(responses.success_true)
        response.update({"result": create_response(collection)})
        return jsonify(response)
