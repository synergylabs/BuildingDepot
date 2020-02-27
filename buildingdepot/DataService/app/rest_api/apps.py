"""
DataService.rest_api.apps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying app models.
It handles the registration and deletion of apps from the system.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask.views import MethodView
from flask import request, jsonify
from ..models.ds_models import Application
from uuid import uuid4
from .. import r, oauth, exchange
from .helper import connect_broker, get_email, check_oauth
from . import responses

import sys
import traceback


class AppService(MethodView):
    @check_oauth
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
            return jsonify(responses.missing_parameters)
        apps = Application._get_collection().find({"user": email})
        if apps.count() == 0:
            app_list = []
        else:
            app_list = apps[0]["apps"]
        return jsonify({"success": "True", "app_list": app_list})

    @check_oauth
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
        json_data = request.get_json()["data"]
        try:
            name = json_data["name"]
        except KeyError:
            return jsonify(responses.missing_parameters)
        apps = Application._get_collection().find({"user": email})

        if apps.count() != 0:
            app_list = apps[0]["apps"]
            for app in app_list:
                if name == app["name"]:
                    return jsonify({"success": "True", "app_id": app["value"]})

        pubsub = connect_broker()
        if pubsub is None:
            return jsonify(responses.broker_connection_failure)

        try:
            channel = pubsub.channel()
            result = channel.queue_declare(durable=True)
        except Exception as e:
            print "Failed to create queue " + str(e)
            print traceback.print_exc()
            if channel:
                channel.close()
            return jsonify(responses.queue_creation_failure)

        if apps.count() == 0:
            Application(
                user=email, apps=[{"name": name, "value": result.method.queue}]
            ).save()
        else:
            app_list.append({"name": name, "value": result.method.queue})
            Application.objects(user=email).update(set__apps=app_list)

        if pubsub:
            try:
                channel.close()
                pubsub.close()
            except Exception as e:
                print "Failed to end RabbitMQ session" + str(e)

        return jsonify({"success": "True", "app_id": result.method.queue})

    @check_oauth
    def delete(self):
        """
        Delete one of current user's applications with the given name.

        Args:
            name (str): name of the application

        Returns (JSON):
            {
                "success" True or False
                "error": details of an error if it happens
            }
        """
        # get current user's list of applications
        email = get_email()
        apps = Application._get_collection().find({"user": email})

        name = ""

        json_data = request.get_json()
        if "data" not in json_data.keys():
            return jsonify(responses.missing_parameters)
        elif "name" not in json_data["data"].keys():
            return jsonify(responses.missing_parameters)
        else:
            name = json_data["data"]["name"]

        app_to_be_deleted = None

        # check whether there is an application with the given name
        # case 1 - there is already an application instance for the given user
        if apps.count() > 0:
            app_filter = filter(lambda x: x["name"] == name, apps[0]["apps"])

            if len(app_filter) > 0:
                app_to_be_deleted = app_filter[0]

        # If there is no application to be delted
        if app_to_be_deleted is None:
            return jsonify(responses.application_does_not_exist)

        pubsub = connect_broker()
        if pubsub is None:
            return jsonify(responses.broker_connection_failure)

        try:
            channel = pubsub.channel()

            if "value" in app_to_be_deleted.keys():
                result = channel.queue_delete(queue=app_to_be_deleted["value"])

            new_app_list = list(filter(lambda x: x["name"] != name, apps[0]["apps"]))
            Application.objects(user=email).update(set__apps=new_app_list)

        except Exception as e:
            print "Failed to delete queue " + str(e)
            print traceback.print_exc()

            if channel:
                channel.close()
            return jsonify(responses.queue_deletion_failure)

        if pubsub:
            try:
                channel.close()
                pubsub.close()
            except Exception as e:
                print "Failed to end RabbitMQ session" + str(e)

        return jsonify(responses.success_true)
