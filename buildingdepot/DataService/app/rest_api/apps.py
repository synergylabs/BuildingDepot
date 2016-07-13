"""
DataService.rest_api.apps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying app models.
It handles the registration and deletion of apps from the system.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask.views import MethodView
from flask import request,jsonify
from ..models.ds_models import Application
from uuid import uuid4
from .. import r,oauth, exchange
from .helper import connect_broker

import sys,traceback

class AppService(MethodView):

    @oauth.require_oauth()
    def get(self):
        """
        Args as data:
            None
        Returns (JSON):
        {
            "success": <True or False>
            "error": <If success if False then reason for failure>
            "app_list": < If succesful, list of registered apps for user>
        }
        """
        email = get_email()
        if email is None:
            return jsonify({'success': 'False', 'error': 'Missing parameters'})
        apps = Application._get_collection().find({'user': email})
        return jsonify({'success': 'True', 'app_list': apps[0]['apps']})

    @oauth.require_oauth()
    def post(self):
        """
        Args as data:
            "name" : <name of app>
        Returns (JSON):
        {
            "success": <True or False>
            "error": <If success if False then reason for failure>
            "app_id": <id of the registered application>
        }
        """
        email = get_email()
        json_data = request.get_json()
        try:
            name = json_data['name']
        except KeyError:
            return jsonify({'success': 'False', 'error': 'Missing parameters'})
        apps = Application._get_collection().find({'user': email})

        if apps.count() != 0:
            app_list = apps[0]['apps']
            for app in app_list:
                if name == app['name']:
                    return jsonify({'success': 'True', 'app_id': app['value']})

        pubsub = connect_broker()
        if pubsub is None:
            return jsonify({'success': 'False', 'error': 'Failed to connect to broker'})

        try:
            channel = pubsub.channel()
            result = channel.queue_declare(durable=True)
        except Exception as e:
            print "Failed to create queue " + str(e)
            print traceback.print_exc()
            if channel:
                channel.close()
            return jsonify({'success': 'False', 'error': 'Failed to create queue'})

        if apps.count() == 0:
            Application(user=email, apps=[{'name': name, 'value': result.method.queue}]).save()
        else:
            app_list.append({'name': name, 'value': result.method.queue})
            Application.objects(user=email).update(set__apps=app_list)

        if pubsub:
            try:
                channel.close()
                pubsub.close()
            except Exception as e:
                print "Failed to end RabbitMQ session" + str(e)

        return jsonify({'success': 'True', 'app_id': result.method.queue})
