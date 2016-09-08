"""
DataService.rest_api.timeseries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the class for the domain service for time-series data. It
handles all the logic for inserting a data value and reading from the underlying
data stores.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""
from flask.views import MethodView
from flask import request, jsonify
from . import responses
from .. import r, influx, oauth, exchange
from .helper import jsonString, timestamp_to_time_string
from .helper import connect_broker
import sys, time, influxdb

sys.path.append('/srv/buildingdepot')
from ..api_0_0.resources.utils import authenticate_acl, permission


class TimeSeriesService(MethodView):
    @oauth.require_oauth()
    @authenticate_acl('r')
    def get(self, name):
        """Reads the time series data of the sensor over the interval specified and returns it to the
           user. If resolution is also specified then data points will be averaged over the resolution
           period and returned

           Args as data:
            "name" : <sensor uuid>
            "start_time" : <unix timestamp of start time>
            "end_time" : <unix timestamp of end time>
            "resolution" : <optional resolution can be specified to scale down data"

           Returns (JSON):
           {
                "data": {
                        "series" : [
                            "columns" : [column definitions]
                        ]
                        "name": <sensor-uuid>
                        "values" : [list of sensor values]
                }
                "success" : <True or False>
           }
        """

        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        resolution = request.args.get('resolution')

        if not all([start_time, end_time]):
            return jsonify(responses.missing_parameters)

        if resolution != None:
            try:
                data = influx.query(
                    'select mean(value) from "' + name + '" where (time>\'' + timestamp_to_time_string(
                        float(start_time)) \
                    + '\' and time<\'' + timestamp_to_time_string(
                        float(end_time)) + '\')' + " GROUP BY time(" + resolution + ")")
            except influxdb.exceptions.InfluxDBClientError:
                return jsonify(responses.resolution_high)
        else:
            data = influx.query(
                'select * from "' + name + '" where time>\'' + timestamp_to_time_string(float(start_time)) \
                + '\' and time<\'' + timestamp_to_time_string(float(end_time)) + '\'')
            response = dict(responses.success_true)
            response.update({'data': data.raw})
        return jsonify(response)

    @oauth.require_oauth()
    def post(self):
        """
        Args as data:
            [
                {
                    "sensor_id":
                    "samples":[
                            {
                                "time": A unix timestamp of a sampling
                                "value": A sensor value
                            },
                            { more times and values }
                        ]
                },
                { more sensors }
            ]
        Returns:
            {
                "success": True or False
                "error": details of an error if it happends
            }
        """

        pubsub = connect_broker()
        if pubsub:
            try:
                channel = pubsub.channel()
            except Exception as e:
                print "Failed to open channel" + " error" + str(e)

        try:
            json = request.get_json()
            points = []
            for sensor in json:
                # check a user has permission
                unauthorised_sensor = []
                print sensor,sensor['sensor_id']
                if permission(sensor['sensor_id']) in ['r/w', 'r/w/p']:
                    for sample in sensor['samples']:
                        dic = {
                            'measurement': sensor['sensor_id'],
                            'time': timestamp_to_time_string(sample['time']),
                            'fields': {
                                'inserted_at': timestamp_to_time_string(time.time()),
                                'value': sample['value']
                            }
                        }
                        points.append(dic)
                    try:
                        channel.basic_publish(exchange=exchange, routing_key=sensor['sensor_id'], body=str(dic))
                    except Exception as e:
                        print "except inside"
                        print "Failed to write to broker " + str(e)
                else:
                    unauthorised_sensor.append(sensor['sensor_id'])
        except KeyError:
            abort(400)

        result = influx.write_points(points)
        if result:
            if len(unauthorised_sensor) > 0:
                response = dict(responses.success_false)
                response.update({'unauthorised_sensor': unauthorised_sensor,
                                 'error': 'Unauthorised sensors present'})
            else:
                response = dict(responses.success_true)
        else:
            response = dict(responses.success_false)
            response.update({'error': 'Error in writing in InfluxDB'})

        if pubsub:
            try:
                channel.close()
                pubsub.close()
            except Exception as e:
                print "Failed to end RabbitMQ session" + str(e)

        return jsonString(response)
