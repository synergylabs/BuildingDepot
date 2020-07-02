"""
DataService.rest_api.permission_request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module queues permission requests for the owner of a mite, and allows the owner
of a mite to get permission requests.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask import request, jsonify
from flask.views import MethodView
from .. import responses
from ...models.cs_models import Sensor, User
from ...auth.views import Client, Token
from ..helper import form_query, create_response, check_oauth, get_email
from ... import oauth, influx
import json

class PermissionRequestService(MethodView):

    @check_oauth
    def get(self):
        data = request.get_json()['data']
        timestamp_filter = data['timestamp_filter']
        email = get_email()

        query = "SELECT parent_device, requested_sensors, requester_email, requester_name FROM $email_permission_requests"

        if timestamp_filter is not None:
            query += " WHERE time >= $time_filter"
        else:
            timestamp_filter = 0

        results = influx.query(query, params={}, bind_params={'email': email, 'time_filter': timestamp_filter})

        request_results = {'requests': []}

        for result in results['results']:
            print str(result)
            for timeseries in result['series']:
                parent_device = timeseries[1]
                requested_sensors = timeseries[2]
                requester_email = timeseries[3]
                requester_name = timeseries[4]
                request_results['requests'].add({'requester_email': requester_email, 'requested_sensors': requested_sensors, 'requester_name': requester_name, 'parent_device': parent_device})

        response = dict(responses.success_true)
        response.update(request_results)
        return jsonify(response)
