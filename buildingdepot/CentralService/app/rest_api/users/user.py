"""
CentralService.rest_api.user
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the interactions with the user models. Takes care
of all the CRUD operations on users. Whenever a new user is registered
an email is sent out to the specified id with a temporary password that
will have to be changed on first login.

@copyright: (c) 2020 SynergyLabs
@license: CMU License. See License file for details.
"""

import uuid
from flask import request, jsonify, current_app
from flask.views import MethodView
from werkzeug.security import generate_password_hash

from .. import responses
from ..helper import get_email, send_mail_gmail, send_local_smtp, check_oauth
from ... import oauth, r
from ...auth.access_control import super_required
from ...auth.views import Client, Token
from ...models.cs_models import User


class UserService(MethodView):
    @check_oauth
    @super_required
    def post(self):
        """
        Adds a new user. Only a super user can add any user. Defauit user
        cannot add any user.

        Note:
            Since this function is decorated with "super_required", we can
            assume that the requester is a super user. We do not need to
            additionally check whether the requester is a super user.

        Args as data:
            first_name (str) : <first name of the new user>
            last_name (str) : <last name of the new user>
            email (str) : <email address of the new user>
            role (str) : <role of the new user. either "default" or "super">

        Returns (JSON) :
            {
                "success": True or False,
                "error": details of an error if it happends
            }
        """

        # check whether the received request has data
        try:
            data = request.get_json()["data"]
        except KeyError:
            return jsonify(responses.missing_data)

        # extract all parameters contained in the data
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        role = data.get("role")

        # check whether all the parameters are appropriately received
        if not all((email, first_name, last_name, role)):
            return jsonify(responses.missing_parameters)

        # check whether the email address is already in use
        if User.objects(email=email).first():
            return jsonify(responses.user_exists)

        # check whether ther role is well formed
        if role not in ["default", "super"]:
            return jsonify(responses.invalid_user_role)

        # register the user finally
        self.register_user(first_name, last_name, email, role)

        # cache superuser in redis
        if role == "super":
            r.sadd("superusers", email)

        return jsonify(responses.success_true)

    @check_oauth
    @super_required
    def get(self, email):
        """
        Get information about a user. Only a super user can get information
        about default users. Default users should not get information about
        other default users. Super users cannot get information about other
        Super users.

        Note:
            Since this function is decorated with "super_required," we can
            assume that the requester is a super user. We do not need to
            additionally check whether the requester is a super user.

        Args:
            email (str) : email address of the user

        Returns (JSON):
            {
                "success": True of False
                "error": details of an error if it happens
                "email": email of the specified user
                "first_name": first name of the specified user
                "last_name": last name of the specified user
                "role": role of the specified user
            }
        """

        # lookup user table
        user = User.objects(email=email).first()

        # check whether the target user exists
        if user is None:
            return jsonify(responses.invalid_user)

        # check whether the target user is a super user
        if user.role == "super":
            return jsonify(responses.unauthorized_user_lookup)

        # send out information
        response = dict(responses.success_true)
        response.update(
            {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
            }
        )

        return jsonify(response)

    @check_oauth
    @super_required
    def delete(self, email):
        """
        Delete a user from CentralService. Only a super user can delete other
        users.

        Note:
            Since this function is decorated with "super_required," we can
            assume that the requester is a super user. We do not need to
            additionally check whether the requester is a super user.

        Args:
            email (str) : email address of the user

        Returns (JSON):
            {
                "success": True of False
                "error": details of an error if it happens
            }
        """

        # fetch a user to delete
        user = User.objects(email=email).first()

        # check whether the specified user exists
        if user is None:
            return jsonify(responses.invalid_user)

        # Remove client object
        Client._get_collection().remove({"user": email})

        # Find token objects
        tokens = Token._get_collection().find({"email": email})

        p = r.pipeline()
        if user.role == "super":
            p.srem("superusers", email)

        # Remove tokens
        for token in tokens:
            p.delete("".join(["oauth:", token.access_token]))
            token.delete()
        p.execute()

        # delete the user
        user.delete()

        return jsonify(responses.success_true)

    def register_user(self, first_name, last_name, email, role):
        """
        Register a user to database and send an email to the newly added user.

        Args:
            first_name (str) : first name of the new user
            last_name (str) : last name of the new user
            email (str) : email address of the new user
            role (str) : role of the new user
        """
        # generate a temporary password
        password = str(uuid.uuid4())

        # create a user with given information
        User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            password=generate_password_hash(password),
        ).save()

        # if email client is specified, send an email to the new user
        if current_app.config["EMAIL"] == "GMAIL":
            send_mail_gmail(first_name + " " + last_name, email, password)
        elif current_app.config["EMAIL"] == "LOCAL":
            send_local_smtp(first_name + " " + last_name, email, password)
