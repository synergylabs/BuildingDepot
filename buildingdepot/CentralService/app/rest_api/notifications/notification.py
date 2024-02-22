"""
DataService.rest_api.notifcation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles setting up and managing notifications for a given ID.

@copyright: (c) 2021 SynergyLabs
@license: CMU License. See License file for details.
"""

from flask import request, jsonify, Flask
from flask.views import MethodView

from .. import responses
from ..helper import check_oauth, get_email
from ...auth.views import Client, Token
from ...models.cs_models import NotificationClientId


def get_notification_client_id(client_email):
    notification_client = NotificationClientId.objects(email=client_email).first()

    if notification_client is not None:
        return notification_client.client_id

    return None


class NotificationClientIdService(MethodView):
    @check_oauth
    def post(self):
        data = request.get_json()["data"]
        print("We got the request")
        print("Want to save the ID " + data["id"])
        if data is None or data["id"] is None:
            return jsonify(responses.missing_parameters)
        print("No params missing")
        if get_notification_client_id(get_email()) is None:
            print("Saving the ID for client " + str(get_email()))
            NotificationClientId(email=get_email(), client_id=data["id"]).save()
        else:
            return jsonify(responses.client_id_already_exists)

        return jsonify(responses.success_true)

    @check_oauth
    def put(self):
        data = request.get_json()["data"]

        if data is None or data["id"] is None:
            return jsonify(responses.missing_parameters)
        try:
            notifications_collection = NotificationClientId.objects(
                email=get_email()
            ).first()
            notifications_collection.update_one(set__client_id=data["id"])
        except RuntimeError as error:
            print("Error", error)

        return jsonify(responses.success_true)
