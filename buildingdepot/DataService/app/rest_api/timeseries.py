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
from flask import request, jsonify, abort
from . import responses
from .. import r, influx, oauth, exchange
from .helper import jsonString, timestamp_to_time_string, check_oauth, get_email
from .helper import connect_broker
import sys, time, influxdb

sys.path.append('/srv/buildingdepot')
from ..api_0_0.resources.utils import authenticate_acl, permission, batch_permission_check


class TimeSeriesService(MethodView):
    @check_oauth
    @authenticate_acl('r')
    def get(self, name):
        """Reads the time series data of the sensor over the interval specified and returns it to the
           user. If resolution is also specified then data points will be averaged over the resolution
           period and returned

           Args as data:
            "name" : <sensor uuid>
            "start_time" : <unix timestamp of start time>
            "end_time" : <unix timestamp of end time>
            "resolution" : <optional resolution can be specified to scale down data",
            "fields" : "<field1>;<feild2>"

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
           Note: 'columns' = ['time', 'mean_value',
                              'mean_200_hz_magnitude', 'mean_200_hz_phase']
        """

        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        resolution = request.args.get('resolution')
        fields= request.args.get('fields')
        if fields:
            fields = fields.split(';')
            fields = '"' + '", "'.join(fields) + '"'
        else:
            fields = '*'

        if not all([start_time, end_time]):
            return jsonify(responses.missing_parameters)

        if resolution:
            if fields == '*':
                return jsonify('TODO: Fields are not supported with resolution')
            try:
                data = influx.query(
                    'select mean(*) from "' + name + '" where (time>\'' + timestamp_to_time_string(
                        float(start_time)) \
                    + '\' and time<\'' + timestamp_to_time_string(
                        float(end_time)) + '\')' + " GROUP BY time(" + resolution + ")")
            except influxdb.exceptions.InfluxDBClientError:
                return jsonify(responses.resolution_high)
            #rawdata = data.raw
        else:
            data = influx.query(
                'select ' + fields + ' from "' + name + '" where time>\'' + timestamp_to_time_string(float(start_time)) \
                + '\' and time<\'' + timestamp_to_time_string(float(end_time)) + '\'')
        response = dict(responses.success_true)
        response.update({'data': data.raw})
        return jsonify(response)

    @check_oauth
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
                                "<freq>_hz_magnitude": freq domain magnitude corresponding to <freq>Hz
                                "<freq>_hz_phase": freq domain phase corresponding to <freq> Hz

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

        pubsub = None

        try:
            postData = request.get_json()
            if "data" in postData:
                json = postData['data']
            else:
                json = postData
            points = []
            sensors_list = [sensor['sensor_id'] for sensor in json]
            permissions = batch_permission_check(sensors_list, get_email())
            # Check if there are any apps associated with the sensors
            pipeline = r.pipeline()
            for sensor in sensors_list:
                pipeline.exists(''.join(['apps:', sensor]))
            apps = dict(zip(sensors_list, pipeline.execute()))
            for sensor in json:
                # check a user has permission
                unauthorised_sensor = []
                # If 'w' (write is in the permission), authorize
                if 'w' in permissions[sensor['sensor_id']]:
                    for sample in sensor['samples']:
                        dic = {
                            'measurement': sensor['sensor_id'],
                            'time': timestamp_to_time_string(sample['time']),
                            'fields': {
                                'inserted_at': timestamp_to_time_string(time.time()),
                                #'value': sample['value']
                            }
                        }
                        del sample['time']
                        # Key assertion TODO: need to raise appropriate error
                        for k in sample.keys():
                            assert k=='value' or \
                                    '_'.join(k.split('_')[1:]) in \
                                    ['hz_magnitude', 'hz_phase']
                        dic['fields'].update(sample)
                        points.append(dic)
                    if apps[sensor['sensor_id']]:
                        if not pubsub:
                            pubsub = connect_broker()

                            if pubsub:
                                try:
                                    channel = pubsub.channel()
                                except Exception as e:
                                    print "Failed to open channel" + " error" + str(e)
                        try:
                            channel.basic_publish(exchange=exchange, routing_key=sensor['sensor_id'], body=str(dic))
                        except Exception as e:
                            print "except inside"
                            print "Failed to write to broker " + str(e)
                else:
                    unauthorised_sensor.append(sensor['sensor_id'])
        except KeyError:
            print json
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

        return jsonify(response)
