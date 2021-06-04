"""
DataService.rest_api.apps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying app models.
It handles the registration and deletion of apps from the system.

@copyright: (c) 2020 SynergyLabs
@license: CMU License. See License file for details.
"""

import sys
import traceback
from flask import request, jsonify
from flask.views import MethodView
from uuid import uuid4

from . import responses
from .helper import connect_broker, get_email, check_oauth
from .. import r, oauth, exchange
from ..models.ds_models import Application


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
            "app_list": < If successful, list of registered apps for user>
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
            "name" : <name of app> or [<name of app>]
        Returns (JSON):
        {
            "success": <True or False>
            "error": <If success if False then reason for failure>
            "app_id": <id of the registered application> or
                     [<ids of the registered application>]
        }
        """
        email = get_email()
        error_flag = False

        json_data = request.get_json()
        if "data" not in json_data.keys():
            return jsonify(responses.missing_parameters)
        elif "name" not in json_data["data"].keys():
            return jsonify(responses.missing_parameters)
        else:
            name = json_data["data"]["name"]

        apps = Application._get_collection().find({"user": email})
        app_list = []
        json_result = {}
        if apps.count() != 0:
            app_list = apps[0]["apps"]
            if not isinstance(name, list):
                for app in app_list:
                    if name == app["name"]:
                        return jsonify({"success": "True", "app_id": app["value"]})
            else:
                json_result = {}
                for app in app_list:
                    for nm in name:
                        if nm == app["name"]:
                            json_result[nm] = {
                                "success": "True",
                                "app_id": app["value"],
                            }

                if len(json_result.keys()) == len(name):
                    return jsonify({"success": "True", "app_id": json_result})

        pubsub = connect_broker()
        if pubsub is None:
            return jsonify(responses.broker_connection_failure)

        if not isinstance(name, list):
            channel = None
            try:
                channel = pubsub.channel()
                result = channel.queue_declare(durable=True)
            except Exception as e:
                print("Failed to create queue " + str(e))
                print(traceback.print_exc())
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
                    print("Failed to end RabbitMQ session" + str(e))

            return jsonify({"success": "True", "app_id": result.method.queue})

        elif isinstance(name, list):
            if not app_list:
                app_list = []
            for nm in name:
                channel = None
                try:
                    channel = pubsub.channel()
                    result = channel.queue_declare(durable=True)

                    json_result[nm] = {}
                    json_result[nm] = {"success": "True"}
                    json_result[nm]["app_id"] = result.method.queue

                    app_list.append({"name": nm, "value": result.method.queue})

                except Exception as e:
                    print("Failed to create queue " + str(e))
                    print(traceback.print_exc())
                    if channel:
                        channel.close()
                    error_flag = True
                    json_result[nm] = {
                        "success": "False",
                        "error": "Failed to create queue",
                    }

            if pubsub:
                try:
                    channel.close()
                    pubsub.close()
                except Exception as e:
                    print("Failed to end RabbitMQ session" + str(e))

            if apps.count() == 0:
                Application(user=email, apps=app_list).save()
            else:
                Application.objects(user=email).update(set__apps=app_list)

            if error_flag:
                return jsonify({"success": "False", "app_id": json_result})
            else:
                return jsonify({"success": "True", "app_id": json_result})

        return jsonify(responses.success_false)

    @check_oauth
    def delete(self):
        """
        Delete one of current user's applications with the given name.

        Args:
            name (str): name of the application or [<name of app>]

        Returns (JSON):
            {
                "success" True or False
                "error": details of an error if it happens
                or
                "name": <ID, "success" True or False>
            }
        """
        # get current user's list of applications
        email = get_email()
        apps = Application._get_collection().find({"user": email})

        app_to_be_deleted = []
        json_result = {}
        error_flag = False
        channel = None
        name = ""

        json_data = request.get_json()
        if "data" not in json_data.keys():
            return jsonify(responses.missing_parameters)
        elif "name" not in json_data["data"].keys():
            return jsonify(responses.missing_parameters)
        else:
            name = json_data["data"]["name"]

        # check whether there is an application with the given name
        # case 1 - there is already an application instance for the given user
        if apps.count() > 0:
            if not isinstance(name, list):
                app_to_be_deleted = None
                app_filter = filter(lambda x: x["name"] == name, apps[0]["apps"])

                if len(app_filter) > 0:
                    app_to_be_deleted = app_filter[0]
            else:
                app_to_be_deleted = []
                json_result = {}
                error_flag = False
                for nm in name:
                    app_filter = filter(lambda x: x["name"] == nm, apps[0]["apps"])
                    if len(app_filter) > 0:
                        app_to_be_deleted.append(app_filter[0])
                    else:
                        json_result[nm] = {
                            "success": "False",
                            "error": "Application does not exist",
                        }
                        error_flag = True

        # If there is no application to be deleted
        if app_to_be_deleted is None:
            return jsonify(responses.application_does_not_exist)

        pubsub = connect_broker()
        if pubsub is None:
            return jsonify(responses.broker_connection_failure)

        if not isinstance(name, list):
            try:
                channel = pubsub.channel()

                if "value" in app_to_be_deleted.keys():
                    result = channel.queue_delete(queue=app_to_be_deleted["value"])

                new_app_list = list(
                    filter(lambda x: x["name"] != name, apps[0]["apps"])
                )
                Application.objects(user=email).update(set__apps=new_app_list)

            except Exception as e:
                print("Failed to create queue " + str(e))
                print(traceback.print_exc())
                if channel:
                    channel.close()
                return jsonify(responses.queue_creation_failure)

            if pubsub:
                try:
                    channel.close()
                    pubsub.close()
                except Exception as e:
                    print("Failed to end RabbitMQ session" + str(e))

            return jsonify(responses.success_true)

        elif isinstance(name, list):
            for app_to_delete in app_to_be_deleted:
                try:
                    channel = pubsub.channel()
                    if "value" in app_to_delete.keys():
                        result = channel.queue_delete(queue=app_to_delete["value"])

                    json_result[app_to_delete["name"]] = {}
                    json_result[app_to_delete["name"]] = {"success": "True"}

                except Exception as e:
                    print("Failed to create queue " + str(e))
                    print(traceback.print_exc())
                    if channel:
                        channel.close()
                    error_flag = True
                    json_result[app_to_delete["name"]] = {
                        "success": "False",
                        "error": "Failed to create queue",
                    }

            new_app_list = list(
                filter(lambda x: x["name"] not in name, apps[0]["apps"])
            )
            Application.objects(user=email).update(set__apps=new_app_list)

            if pubsub:
                try:
                    if channel:
                        channel.close()
                    pubsub.close()
                except Exception as e:
                    print("Failed to end RabbitMQ session" + str(e))

            if error_flag:
                return jsonify({"success": "False", "name": json_result})
            else:
                return jsonify({"success": "True", "name": json_result})

        return jsonify(responses.success_false)
