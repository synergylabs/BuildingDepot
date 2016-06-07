"""
DataService.rest_api.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains all the definitions for the REST api's that are exposed to the user.
All requests will need to be authenticated using an OAuth token and sensor specific
requests will also have an additional check where the ACL's are referenced to see if
the user has access to the specific sensor

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask import json, render_template, abort, session
from flask import request, redirect, url_for, jsonify, flash
from . import api
from ..models.ds_models import *
from ..service.utils import *
from uuid import uuid4
from .. import r, influx, oauth, exchange, permissions
from werkzeug.security import gen_salt
import sys, time, influxdb, urllib, traceback, pika
from helper import create_response
from instrument import instrument

sys.path.append('/srv/buildingdepot')
from utils import get_user_oauth
from ..api_0_0.resources.utils import *
from ..api_0_0.resources.acl_cache import invalidate_user, invalidate_permission

@instrument
@api.route('/sensor/list', methods=['GET'])
@oauth.require_oauth()
def get_sensors_metadata():
    """ If request type is params all the sensors with the specified paramter key and values are returned,
        for request type of tags all the sensors with the matching tag key and value are searched for and
        returned, similarly for metadata

        Args as data:

        "filter" : <Type of filter e.g. tags or metadata>
        "param": "value"

        Returns (JSON):
        {
          "data": [
            {
              "building": <building name>,
              "metadata": {
                    "metadata-name":"metadata value
                    .
                    .
                    <metadata key value pairs>
              },
              "name": <uuid of sensor>,
              "source_identifier": <identifier of sensor>,
              "source_name": <Sensor source name>,
              "tags": [
                {
                  "name": <name of tag>,
                  "value": <value of tag>
                }
                .
                .
                .
                <tag key value pairs>
              ]
            }
          ]
        }
    """
    request_type = request.args.get('filter')
    if (request_type is None) or (len(request.args) < 2):
        return jsonify({'success': 'False', 'error': 'Missing parameters'})

    for key, val in request.args.iteritems():
        if key != 'filter':
            param = urllib.unquote(key).decode('utf8')
            value = urllib.unquote(val).decode('utf8')
            print param, value

    if request_type == "params":
        list_sensors = Sensor._get_collection().find({param: value})
        return jsonify({'data': create_response(list_sensors)})
    elif request_type == "tags":
        list_sensors = Sensor._get_collection().find({request_type: {'name': param, 'value': value}})
        return jsonify({'data': create_response(list_sensors)})
    elif request_type == "metadata":
        list_sensors = Sensor._get_collection().find({request_type + "." + param: value})
        return jsonify({'data': create_response(list_sensors)})
