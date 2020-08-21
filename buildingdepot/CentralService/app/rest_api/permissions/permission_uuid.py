"""
DataService.rest_api.permission
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying permission models.
It handles the required CRUD operations for permissions.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask import request, jsonify, Flask
from flask.views import MethodView
from .. import responses
from ...models.cs_models import User
from ..helper import form_query, create_response, check_oauth, get_email
from ... import oauth
import traceback, json, hashlib, uuid

class PermissionRequestUUIDService(MethodView):
    @check_oauth
    def get(self):
        email = get_email()
        results = User._get_collection().find({"email": email})

        response = dict(responses.success_true)

        for user in results:
            response.update({'id': str(user['_id'])})

        return jsonify(response)
