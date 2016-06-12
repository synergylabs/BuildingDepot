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

from .helper import get_email
from . import responses
import uuid


class UserService(MethodView):
    def post(self):
        try:
            data = request.get_json()['data']
        except KeyError:
            return jsonify(responses.missing_data)

        email = data.get('email')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        role = data.get('role')

        if User.objects(email=email).first() is None:
            return jsonify(responses.user_exists)

        if role == 'super':
            if User.objects(email=get_email()).first().role == 'super':
                self.register_user(email, 'super')
            else:
                return jsonify(responses.unauthorized_user)
        self.register_user('default')
        return jsonify(response.success_true)

    def register_user(email, role):
        password = generate_password_hash(uuid.uuid4())
        User(email=email,
             first_mame=first_name, last_name=last_name,
             role=role, password=password).save()
        send_registration_email(email, password)

    def get(self, name):
        user = User.objects(email=get_email()).first()
        if user is None:
            return jsonify(responses.invalid_user)

        response = dict(responses.success_true)
        response.update({'email': user.email,
                         'first_name': user.first_name,
                         'last_name': user.last_name,
                         'role': user.role})
        return jsonify(response)
