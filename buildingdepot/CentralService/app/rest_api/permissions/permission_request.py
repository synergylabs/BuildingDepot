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
from datetime import datetime
import json

class PermissionRequestService(MethodView):

    def to_list_of_strings(self, unicode_string):
        return unicode_string.replace("u'", "").replace("'", "").replace("[", "").replace("]", "").encode(encoding="ascii").split(", ")

    @check_oauth
    def get(self):
        """
        Get log of permission requests. Takes optional query param timestamp_filter. If no param is provided, all requests are returned.

        Args as query param:
        timestamp_filter : <unix timestamp in milliseconds to start getting requests>

        Returns (JSON):
        {
            'requests': [{
                'parent_device': str(UUID of device that contains sensors to get permission),
                'requested_sensors': ['UUID of requested sensor'],
                'requester_email': str(email of person requesting permission to sensors),
                'requester_name': str(first and last name of person requesting permission to sensors)
            }]
        }
        """
        email = get_email()
        timestamp_filter = 0

        if request.args.get('timestamp_filter') is not None:
            timestamp_filter = int(request.args.get('timestamp_filter'))

        #timestamp_filter = datetime.fromtimestamp(float(timestamp_filter) / 100).isoformat("T") + "Z"
        ns_in_ms = 1000000
        timestamp_filter = str(timestamp_filter * ns_in_ms)

        query = 'SELECT parent_device, requested_sensors, requester_email, requester_name FROM "' + email + '_permission_requests" WHERE time >= ' + timestamp_filter
        request_results = {'requests': []}

        results = influx.query(query)

        try:
            items = results.items()[0]

            for result in items[1]:
                print str(result)
                parent_device = result["parent_device"]
                requested_sensors = self.to_list_of_strings(result["requested_sensors"])
                requester_email = result["requester_email"]
                requester_name = result["requester_name"]
                request_results['requests'].append({'requester_email': requester_email, 'requested_sensors': requested_sensors, 'requester_name': requester_name, 'parent_device': parent_device})
        except Exception as e:
            print str(e)
            #No items to process - empty query
            pass

        response = dict(responses.success_true)
        response.update(request_results)
        return jsonify(response)
