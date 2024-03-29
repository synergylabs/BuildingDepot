"""
DataService.rest_api.permission
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying permission models.
It handles the required CRUD operations for permissions.

@copyright: (c) 2024 SynergyLabs
@license: CMU License. See License file for details.
"""

import hashlib
import json
import os
import pika
import traceback
from flask import request, jsonify, Flask
from flask.views import MethodView
from pymongo import MongoClient

from .. import responses
from ..helper import form_query, create_response, check_oauth, get_email
from ..notifications.notification import get_notification_client_id
from ..notifications.push_notifications import PushNotification
from ... import oauth, app
from ...auth.views import Client, Token
from ...models.cs_models import Sensor, User, PermissionRequest


class PermissionRequestService(MethodView):
    @check_oauth
    def get(self):
        """
        Get log of permission requests. Takes optional query param timestamp_filter. If no param is provided, all requests are returned.
        Args as query param:
        timestamp_filter : <unix timestamp in milliseconds to start getting requests>
        Returns (JSON):
        {
            'requests': [{
                'parent_device': str(UUID of device that contains sensors to get permission),
                'requested_sensors': ['UUID of requested sensor'],
                'requester_email': str(email of person requesting permission to sensors),
                'requester_name': str(first and last name of person requesting permission to sensors)
            }]
        }
        """
        email = get_email()
        timestamp_filter = 0

        if request.args.get("timestamp_filter") is not None:
            timestamp_filter = int(request.args.get("timestamp_filter"))

        permission_request_history = PermissionRequest.objects(email=email)
        request_results = {"permission_requests": []}

        if permission_request_history is not None:
            for permission_request in permission_request_history:
                timestamp = int(permission_request["timestamp"])

                if timestamp >= timestamp_filter:
                    request_results["permission_requests"].append(
                        permission_request["requests"]
                    )

        response = dict(responses.success_true)
        response.update(request_results)
        return jsonify(response)

    def map_sensors_to_owner(self, target_sensors):
        user_sensor_map = {}

        for sensor_uuid in target_sensors:
            sensor_uuid = sensor_uuid.encode("ascii")
            sensor = Sensor.objects(name=sensor_uuid).first()
            sensor_owner = self.get_user_who_claimed(sensor.tags)

            if sensor_owner is not None:
                if sensor_owner not in user_sensor_map:
                    user_sensor_map[sensor_owner] = []

                user_sensor_map[sensor_owner].append(sensor_uuid)

            else:
                for tag in sensor.tags:
                    if tag.name == "parent":
                        parent_sensor_uuid = tag.value
                        parent_sensor = Sensor.objects(name=parent_sensor_uuid).first()

                        sensor_owner = self.get_user_who_claimed(parent_sensor.tags)

                        if sensor_owner is not None:
                            if sensor_owner not in user_sensor_map:
                                user_sensor_map[sensor_owner] = []

                            user_sensor_map[sensor_owner].append(sensor_uuid)

        return user_sensor_map

    def get_user_who_claimed(self, tags):
        user = None

        for tag in tags:
            if tag.name == "claimed":
                user = tag.value.encode("ascii")

        return user

    def get_sensor_objects_from_uuids(self, uuids):
        sensor_objects = []

        for uuid in uuids:
            sensor = Sensor.objects(name=uuid).first()
            sensor_json = {
                "name": sensor.name.encode("ascii"),
                "source_name": sensor.source_name.encode("ascii"),
                "source_identifier": sensor.source_identifier.encode("ascii"),
                "building": sensor.building.encode("ascii"),
                "tags": {},
            }

            for tags in sensor.tags:
                sensor_json["tags"][tags.name.encode("ascii")] = tags.value.encode(
                    "ascii"
                )

            sensor_objects.append(sensor_json)

        return sensor_objects

    @check_oauth
    def post(self):
        """
        Args:
            target_sensors the individual sensors to request permission to
            timestamp the local time that a permission request occurred
        Returns:
            Success if the operation could be completed
        """
        data = request.get_json()["data"]
        target_sensors = data["target_sensors"]
        timestamp = data["timestamp"]

        if not all([target_sensors, timestamp]):
            return jsonify(responses.missing_parameters)

        requester = User.objects(email=get_email()).first()

        user_sensor_map = self.map_sensors_to_owner(target_sensors)

        for user in user_sensor_map:
            sensors = self.get_sensor_objects_from_uuids(user_sensor_map[user])
            permission_request_data = {
                "requester_name": str(requester.first_name)
                + " "
                + str(requester.last_name),
                "requester_email": str(get_email()),
                "requested_sensors": sensors,
            }
            PermissionRequest(
                email=user,
                timestamp=str(timestamp),
                requests=permission_request_data,
            ).save()

            try:
                for user_db in User._get_collection().find({"email": user}):
                    permission_request_json = json.dumps(permission_request_data)
                    PushNotification.get_instance().send(
                        get_notification_client_id(user),
                        permission_request_json,
                        destination="permission_requests",
                    )

            except Exception as e:
                traceback.print_exc()
                print(str(repr(e)))
                return jsonify(responses.rabbit_mq_bind_error)

        return jsonify(responses.success_true)
