"""
CentralService.rest_api.user
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the interactions with the user models. Takes care
of all the CRUD operations on users. Whenever a new user is registered
an email is sent out to the specified id with a temporary password that
will have to be changed on first login.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from .helper import send_registration_email
from flask import request,jsonify
from flask.views import MethodView
from werkzeug.security import generate_password_hash
from ..models.cs_models import User
from .helper import get_email
from . import responses
from .. import oauth
from ..api_0_0.resources.utils import super_required
import uuid

class UserService(MethodView):

    @oauth.require_oauth()
    def post(self):
        try:
            data = request.get_json()['data']
        except KeyError:
            return jsonify(responses.missing_data)

        email = data.get('email')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        role = data.get('role')

        if not all ((email,first_name,last_name,role)):
            return jsonify(responses.missing_paramters)

        if User.objects(email=email).first():
            return jsonify(responses.user_exists)

        if role=='super':
            if User.objects(email=get_email()).first().role == 'super':
                self.register_user(first_name,last_name,email,'super')
            else:
                return jsonify(responses.unauthorized_user)
        self.register_user(first_name,last_name,email,'default')
        return jsonify(responses.success_true)

    @oauth.require_oauth()
    def get(self,name):
        user = User.objects(email=get_email()).first()
        if user is None:
            return jsonify(responses.invalid_user)

        response = dict(responses.success_true)
        response.update({'email':user.email,
                        'first_name':user.first_name,
                        'last_name':user.last_name,
                        'role':user.role})
        return jsonify(response)

    @oauth.require_oauth()
    @super_required
    def delete(self,name):
        user = User.objects(email=name).first()
        if user is None:
            return jsonify(responses.invalid_user)
        user.delete()
        return jsonify(responses.success_true)

    def register_user(self,first_name,last_name,email,role):
        password = str(uuid.uuid4())
        User(email=email,first_name=first_name,
            last_name=last_name,role=role,
            password=generate_password_hash(password)).save()
        send_registration_email(first_name+" "+last_name,email,password)


