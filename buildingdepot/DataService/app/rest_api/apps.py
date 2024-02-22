"""
DataService.rest_api.apps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying app models.
It handles the registration and deletion of apps from the system.

@copyright: (c) 2024 SynergyLabs
@license: CMU License. See License file for details.
"""

import json
import traceback
from flask import request, jsonify
from flask.views import MethodView

from . import responses
from .helper import connect_broker, get_email, check_oauth
from ..models.ds_models import Application, NodeEncoder


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
        app_objects = Application.objects(user=email).first()
        if not app_objects:
            return jsonify(responses.application_does_not_found_for_user)

        # Use the custom NodeEncoder to handle serialization
        app_list_json = json.dumps(app_objects.apps, cls=NodeEncoder)

        return jsonify({"success": "True", "app_list": json.loads(app_list_json)})

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
        json_data = request.get_json()

        if "data" not in json_data or "name" not in json_data["data"]:
            return jsonify(responses.missing_parameters)

        app_names = json_data["data"]["name"]

        is_list = isinstance(app_names, list)
        if not is_list:
            if app_names is None or app_names == "":
                return jsonify(responses.missing_parameters)
        else:
            if len(app_names) == 0:
                return jsonify(responses.missing_parameters)

        pubsub = None
        json_result = None
        app_list = None
        error_flag = False

        app_objects = Application.objects(user=email).first()

        if app_objects:
            app_list = app_objects.apps

            if not is_list:
                for app in app_list:
                    if app_names == app["name"]:
                        return jsonify({"success": "True", "app_id": app["value"]})
            else:
                json_result = {}
                for app in app_list:
                    for nm in app_names:
                        if nm == app["name"]:
                            json_result[nm] = {
                                "success": "True",
                                "app_id": app["value"],
                            }

                if len(list(json_result.keys())) == len(app_names):
                    return jsonify({"success": "True", "app_id": json_result})

        if not pubsub:
            pubsub = connect_broker()
            if pubsub is None:
                return jsonify(responses.broker_connection_failure)
            else:
                if not is_list:
                    try:
                        channel = pubsub.channel()
                        result = channel.queue_declare(durable=True, queue="")
                    except Exception as e:
                        print(("Failed to create queue " + str(e)))
                        print((traceback.print_exc()))
                        if channel is not None:
                            channel.close()
                        return jsonify(responses.queue_creation_failure)

                    if app_objects:
                        app_list = app_objects.apps
                        app_list.append({"name": app_names, "value": result.method.queue})
                        Application.objects(user=email).update(set__apps=app_list)
                    else:
                        Application(
                            user=email, apps=[{"name": app_names, "value": result.method.queue}]
                        ).save()

                    if pubsub:
                        try:
                            channel.close()
                            pubsub.close()
                        except Exception as e:
                            print(("Failed to end RabbitMQ session" + str(e)))

                    return jsonify({"success": "True", "app_id": result.method.queue})
                else:
                    if json_result is None:
                        json_result = {}
                    if app_list is None:
                        app_list = []

                    for nm in app_names:
                        if nm not in json_result:
                            try:
                                channel = pubsub.channel()
                                result = channel.queue_declare(durable=True, queue="")

                                json_result[nm] = {}
                                json_result[nm] = {"success": "True"}
                                json_result[nm]["app_id"] = result.method.queue

                                app_list.append({"name": nm, "value": result.method.queue})

                            except Exception as e:
                                print(("Failed to create queue " + str(e)))
                                print((traceback.print_exc()))
                                if channel:
                                    channel.close()
                                error_flag = True
                                json_result[nm] = {
                                    "success": "False",
                                    "error": "Failed to create queue",
                                }

                    if pubsub:
                        try:
                            print("close channel pubsub")
                            channel.close()
                            pubsub.close()
                        except Exception as e:
                            print(("Failed to end RabbitMQ session" + str(e)))

                    if app_objects:
                        Application.objects(user=email).update(set__apps=app_list)
                    else:
                        Application(user=email, apps=app_list).save()

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
        app_len = Application._get_collection().count_documents({"user": email})

        app_to_be_deleted = []
        json_result = {}
        error_flag = False
        channel = None

        json_data = request.get_json()
        if "data" not in list(json_data.keys()):
            return jsonify(responses.missing_parameters)
        elif "name" not in list(json_data["data"].keys()):
            return jsonify(responses.missing_parameters)
        else:
            app_name = json_data["data"]["name"]

        # check whether there is an application with the given name
        # case 1 - there is already an application instance for the given user
        if app_len > 0:
            apps = Application._get_collection().find({"user": email})
            if not isinstance(app_name, list):
                app_to_be_deleted = None
                app_filter = [x for x in apps[0]["apps"] if x["name"] == app_name]

                if len(app_filter) > 0:
                    app_to_be_deleted = app_filter[0]
            else:
                # app_name is a list
                app_to_be_deleted = []
                json_result = {}
                error_flag = False
                for nm in app_name:
                    app_filter = [x for x in apps[0]["apps"] if x["name"] == nm]
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

        apps = Application._get_collection().find({"user": email})

        if not isinstance(app_name, list):
            try:
                channel = pubsub.channel()

                if "value" in list(app_to_be_deleted.keys()):
                    result = channel.queue_delete(queue=app_to_be_deleted["value"])

                new_app_list = list([x for x in apps[0]["apps"] if x["name"] != app_name])
                Application.objects(user=email).update(set__apps=new_app_list)

            except Exception as e:
                print(("Failed to create queue " + str(e)))
                print((traceback.print_exc()))
                if channel:
                    channel.close()
                return jsonify(responses.queue_creation_failure)

            if pubsub:
                try:
                    channel.close()
                    pubsub.close()
                except Exception as e:
                    print(("Failed to end RabbitMQ session" + str(e)))

            return jsonify(responses.success_true)

        elif isinstance(app_name, list):
            for app_to_delete in app_to_be_deleted:
                try:
                    channel = pubsub.channel()
                    if "value" in list(app_to_delete.keys()):
                        result = channel.queue_delete(queue=app_to_delete["value"])

                    json_result[app_to_delete["name"]] = {}
                    json_result[app_to_delete["name"]] = {"success": "True"}

                except Exception as e:
                    print(("Failed to create queue " + str(e)))
                    print((traceback.print_exc()))
                    if channel:
                        channel.close()
                    error_flag = True
                    json_result[app_to_delete["name"]] = {
                        "success": "False",
                        "error": "Failed to create queue",
                    }

            new_app_list = list([x for x in apps[0]["apps"] if x["name"] not in app_name])
            Application.objects(user=email).update(set__apps=new_app_list)

            if pubsub:
                try:
                    if channel:
                        channel.close()
                    pubsub.close()
                except Exception as e:
                    print(("Failed to end RabbitMQ session" + str(e)))

            if error_flag:
                return jsonify({"success": "False", "name": json_result})
            else:
                return jsonify({"success": "True", "name": json_result})

        return jsonify(responses.success_false)
