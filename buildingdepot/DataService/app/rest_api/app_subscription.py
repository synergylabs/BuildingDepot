"""
DataService.rest_api.app_subscription
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying app models to
subscribe the sensors that the user requests to the app id specified.
It also accordingly handles the unsubscription of sensors from the apps.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask.views import MethodView
from flask import request, jsonify
from ..models.ds_models import Application
from .. import r, oauth, exchange
import sys, traceback
from .helper import connect_broker, get_email, check_oauth
from . import responses


class AppSubscriptionService(MethodView):

    @check_oauth
    def post(self):
        """
        Create Queue binding of sensor and user's applications with the given name.

        Args as data:
            "app" : <name of app>
            "sensorID": <name of the sensor>
        Returns (JSON):
        {
            "success": <True or False>
            "error": <If success if False then reason for failure>
        }
        """

        json_data = request.get_json()['data']
        email = get_email()
        try:
            app_id = json_data['app']
            sensor = json_data['sensor']
        except Exception as e:
            return jsonify(responses.missing_parameters)

        app_list = Application._get_collection().find({'user': email})[0]['apps']
        pubsub = connect_broker()
        if pubsub is None:
            return jsonify(responses.broker_connection_failure)

        for app in app_list:
            if app_id == app['value']:
                try:
                    channel = pubsub.channel()
                    channel.queue_bind(exchange=exchange, queue=app['value'], routing_key=sensor)
                    r.sadd(''.join(['apps:', sensor]), app['value'])

                except Exception as e:
                    print "Failed to bind queue " + str(e)
                    print traceback.print_exc()
                    return jsonify(responses.queue_binding_failure)

                if pubsub:
                    try:
                        channel.close()
                        pubsub.close()
                    except Exception as e:
                        print "Failed to end RabbitMQ session" + str(e)

            return jsonify(responses.success_true)

        return jsonify(responses.application_does_not_exist)

    @check_oauth
    def delete(self):
        """
        Delete Queue binding of sensor and user's applications with the given name.

        Args as data:
            "app" : <name of app>
            "sensorID": <name of the sensor>
        Returns (JSON):
        {
            "success": <True or False>
            "error": <If success if False then reason for failure>
        }
        """

        json_data = request.get_json()['data']
        email = get_email()
        try:
            app_id = json_data['app']
            sensor = json_data['sensor']
        except Exception as e:
            return jsonify(responses.missing_parameters)

        app_list = Application._get_collection().find({'user': email})[0]['apps']
        pubsub = connect_broker()
        if pubsub is None:
            return jsonify(responses.broker_connection_failure)

        for app in app_list:
            if app_id == app['value']:
                try:
                    channel = pubsub.channel()
                    channel.queue_unbind(exchange=exchange, queue=app['value'], routing_key=sensor)
                    r.srem(''.join(['apps:', sensor]), app['value'])
                except Exception as e:
                    print "Failed to bind queue " + str(e)
                    print traceback.print_exc()
                    return jsonify(responses.queue_binding_failure)

                if pubsub:
                    try:
                        channel.close()
                        pubsub.close()
                    except Exception as e:
                        print "Failed to end RabbitMQ session" + str(e)

            return jsonify(responses.success_true)

        return jsonify(responses.application_does_not_exist)

    # @check_oauth
    # def dispatch_request(self):
    #     json_data = request.get_json()['data']
    #     email = get_email()
    #     try:
    #         app_id = json_data['app']
    #         sensor = json_data['sensor']
    #     except Exception as e:
    #         return jsonify({'success': 'False', 'error': 'Missing parameters'})
    #
    #     app_list = Application._get_collection().find({'user': email})[0]['apps']
    #
    #     pubsub = connect_broker()
    #     if pubsub is None:
    #         return jsonify({'success': 'False', 'error': 'Failed to connect to broker'})
    #
    #     for app in app_list:
    #         if app_id == app['value']:
    #             try:
    #                 channel = pubsub.channel()
    #                 if request.method == 'POST':
    #                     channel.queue_bind(exchange=exchange, queue=app['value'], routing_key=sensor)
    #                     r.sadd(''.join(['apps:', sensor]), app['value'])
    #                 elif request.method == 'DELETE':
    #                     channel.queue_unbind(exchange=exchange, queue=app['value'], routing_key=sensor)
    #                     r.srem(''.join(['apps:', sensor]), app['value'])
    #             except Exception as e:
    #                 print "Failed to bind queue " + str(e)
    #                 print traceback.print_exc()
    #                 return jsonify({'success': 'False', 'error': 'Failed to bind queue'})
    #
    #             if pubsub:
    #                 try:
    #                     channel.close()
    #                     pubsub.close()
    #                 except Exception as e:
    #                     print "Failed to end RabbitMQ session" + str(e)
    #
    #             return jsonify({'success': 'True'})
    #
    #     return jsonify({'success': 'False', 'error': 'App id doesn\'t exist'})
