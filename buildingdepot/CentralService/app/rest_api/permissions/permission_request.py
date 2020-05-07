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
from ..helper import form_query, create_response, check_oauth
from ... import oauth

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
            channel.exchange_declare(exchange='test', exchange_type='direct')
            channel.close()
            return pubsub
        except Exception as e:
            print "Failed to open connection to broker " + str(e)
            return None

    @check_oauth
    def post(self):
        sensor_owner = request.args.get('owner')

        if sensor_owner is None:
            return jsonify(responses.missing_parameters)

        pubsub = connect_broker()
        requester = User._get_collection().find({"email":get_email()})

        try:
            channel = pubsub.channel()
            permission_request_data = json.dumps({ "requester_name": "", "requester_email": get_email() })
            key = (requester.).hexdigest()
            channel.basic_publish(exchange='permission_requests', routing_key=key, body=permission_request_data)
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