"""
DataService.rest_api.permission
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying permission models.
It handles the required CRUD operations for permissions.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask import request, jsonify
from flask.views import MethodView
from .. import responses
from ...models.cs_models import Sensor, User
from ...auth.views import Client, Token
from ..helper import form_query, create_response, check_oauth, get_email, timestamp_to_time_string
from ... import oauth, influx
import traceback, json, hashlib, pika

class PermissionRequestService(MethodView):
    def connect_broker(self):
        """
        Args:
            None:
        Returns:    
            pubsub: object corresponding to the connection with the broker
        """
        try:
            pubsub = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            channel = pubsub.channel()
            channel.exchange_declare(exchange='permission_requests', type='direct')
            channel.close()
            return pubsub
        except Exception as e:
            print "Failed to open connection to broker " + str(e)
            return None

    @check_oauth
    def post(self):
        data = request.get_json()['data']
        parent_sensor = data['parent_sensor']
        target_sensors = data['target_sensors']
        timestamp = data['timestamp']

        if all([parent_sensor, target_sensors, timestamp]):
            return jsonify(responses.missing_parameters)

        email = get_email()
        pubsub = self.connect_broker()
        requester = User.objects(email=get_email()).first()
        sensor_tags = Sensor.objects(name=parent_sensor).first().tags

        sensor_owner = None

        for tag in sensor_tags:
            if tag.name == "claimed":
                sensor_owner = tag.value

        if sensor_owner is None:
            return jsonify(responses.device_not_claimed)

        try:
            clients = Client.objects(user=sensor_owner).order_by('_id')
            client = None

            for curr_client in clients:
                client = curr_client

            if client is None:
                return jsonify(responses.inactive_user)

            channel = pubsub.channel()
            permission_request_data = { "requester_name": str(requester.first_name) + " " + str(requester.last_name), "requester_email": str(email), "parent_device": str(parent_sensor), "requested_sensors": str(target_sensors) }
            permission_request_json = json.dumps(permission_request_data)
            key = hashlib.sha256("1dX0ff43nPt".encode() + sensor_owner.encode() + client.client_id.encode()).hexdigest()
            
            channel.basic_publish(exchange='permission_requests', routing_key=str(key), body=permission_request_json)
            influx.write_points([{'measurement': sensor_owner + "_permission_requests", 'time': int(timestamp), 'fields': permission_request_data}], time_precision="ms")
        except Exception as e:
            traceback.print_exc()
            print str(repr(e))
            return jsonify(responses.rabbit_mq_bind_error)

        if pubsub:
            try:
                channel.close()
                pubsub.close()
            except Exception as e:
                print "Failed to end RabbitMQ session " + str(e)

        return jsonify(responses.success_true)
