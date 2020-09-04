"""
CentralService.oauth_bd.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains all the class and method definitions required for the OAuth
token generation and verification

@copyright: (c) 2020 SynergyLabs
@license: CMU License. See License file for details.
"""

from . import oauth_bd
from .. import oauth, r
from datetime import datetime, timedelta
from flask import Flask, current_app, Blueprint
from flask import session, request
from flask import render_template, redirect, jsonify
from flask_oauthlib.client import OAuth
from werkzeug.security import gen_salt
from bson.objectid import ObjectId
from xmlrpc.client import ServerProxy
from ..rest_api import responses
import sys, os, binascii

from ..models.cs_models import User
from mongoengine import *
from mongoengine.context_managers import switch_db
from uuid import uuid4

expires_in = 34560


class Client(Document):
    client_id = StringField(required=True, unique=True)
    client_secret = StringField(required=True)
    user = StringField()
    _redirect_uris = StringField()
    _default_scopes = StringField()

    @property
    def client_type(self):
        return 'public'

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0]

    @property
    def default_scopes(self):
        if self._default_scopes:
            return self._default_scopes.split()
        return []


class Grant(Document):
    user = StringField()
    client = ReferenceField(Client)
    code = StringField(required=True)
    redirect_uri = StringField()
    expires = DateTimeField()
    _scopes = StringField()

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


class Token(Document):
    client = ReferenceField(Client)
    user = StringField()
    token_type = StringField()
    access_token = StringField(unique=True)
    refresh_token = StringField(unique=True)
    expires = DateTimeField()
    _scopes = StringField()
    email = StringField()

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


def get_user_oauth(email):
    """Check if user email exists for OAuth"""
    user = User.objects(email=email).first()
    if user is not None:
        return str(user.email)
    return None


def current_user():
    if 'email' in session:
        email = session['email']
        return get_user_oauth(email)
    return None


@oauth_bd.route('/', methods=('GET', 'POST'))
def home():
    if request.method == 'POST':
        email = request.form.get('username')
        user = get_user_oauth(email)
        if not user:
            return jsonify({'response': 'Access Denied'})
        session['email'] = user
        return redirect('/')
    user_current = current_user()
    return render_template('home.html', user=user_current)


@oauth_bd.route('/client')
def client():
    user_current = current_user()
    if not user_current:
        return redirect('/')
    item = Client(
        client_id=gen_salt(40),
        client_secret=gen_salt(50),
        _redirect_uris=' '.join([
            'http://localhost:8000/authorized',
            'http://127.0.0.1:8000/authorized',
            'http://127.0.1:8000/authorized',
            'http://127.1:8000/authorized']),
        _default_scopes='email',
        user=get_user_oauth(user_current)).save()
    return jsonify(
        client_id=item.client_id,
        client_secret=item.client_secret
    )


@oauth.clientgetter
def load_client(client_id):
    return Client.objects(client_id=client_id).first()


@oauth.grantgetter
def load_grant(client_id, code):
    return Grant.objects(client=Client.objects(client_id=client_id).first(),
                         code=code).first()


@oauth.grantsetter
def save_grant(client_id, code, request, *args, **kwargs):
    expires = datetime.utcnow() + timedelta(seconds=100)
    grant = Grant(
        client=Client.objects(client_id=client_id).first(),
        code=code['code'],
        redirect_uri=request.redirect_uri,
        _scopes=' '.join(request.scopes),
        user=get_user_oauth(current_user()), expires=expires)
    grant.save()
    return grant


@oauth.tokengetter
def load_token(access_token=None, refresh_token=None):
    if access_token:
        return Token.objects(access_token=access_token).first()
    elif refresh_token:
        return Token.objects(refresh_token=refresh_token).first()


@oauth.tokensetter
def save_token(token, request, *args, **kwargs):
    toks = Token.objects(client=request.client, user=request.user)
    previous_tokens = ['oauth']
    for t in toks:
        previous_tokens.append(''.join(['oauth:', t.access_token]))
        t.delete()
    r.delete(*previous_tokens)
    expires_in = token.pop('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=expires_in)
    tok = Token(
        access_token=token['access_token'],
        refresh_token=token['refresh_token'],
        token_type=token['token_type'],
        _scopes=token['scope'],
        expires=expires,
        client=request.client,
        user=request.user,
        email=request.user).save()
    r.setex(''.join(['oauth:', tok.access_token]), expires_in, client.user)
    return tok


@oauth_bd.route('/access_token/client_id=<client_id>/client_secret=<client_secret>', methods=['GET'])
def get_access_token(client_id, client_secret):
    """ Generates and returns an access token to the user if the client_id and
        client_secret provided by them are valid"""
    client = Client.objects(client_id=client_id, client_secret=client_secret).first()
    if client != None:
        # Set token expiry period and create it
        expires = datetime.utcnow() + timedelta(seconds=expires_in)
        tok = Token(
            access_token=str(binascii.hexlify(os.urandom(16))),
            refresh_token=str(binascii.hexlify(os.urandom(16))),
            token_type='Bearer',
            _scopes='email',
            expires=expires,
            client=client,
            user=client.user,
            email=client.user).save()
        r.setex(''.join(['oauth:', tok.access_token]), expires_in, client.user)
        return jsonify({'success': 'True', 'access_token': tok.access_token})
    return jsonify({'success': 'False', 'access_token': 'Invalid credentials'})


@oauth_bd.route('/generate', methods=['POST'])
def generate_credentials():
    cred = request.get_json()['data']
    print((cred['email'], type(cred)))
    email = cred['email']
    password = cred['password']
    print((email, password))
    user = User.objects(email=email).first()
    if user is not None and user.first_login and user.verify_password(password):
        response = dict(responses.success_true)
        response.update({'login': 'You have logged in for the first time.Please change your\
         password on the UI'})
        return jsonify(response)
    elif user is not None and user.verify_password(password):
        if len(Client.objects(user=email)) > 0:
            keys = [{"client_id": gen_salt(40), "client_secret": gen_salt(50)}]
            item = Client(
                client_id=keys[0]['client_id'],
                client_secret=keys[0]['client_secret'],
                _redirect_uris=' '.join([
                    'http://localhost:8000/authorized',
                    'http://127.0.0.1:8000/authorized',
                    'http://127.0.1:8000/authorized',
                    'http://127.1:8000/authorized']),
                _default_scopes='email',
                user=email).save()
            response = dict(responses.success_true)
            response.update({'client_id': keys[0]['client_id'],
                             'client_key': keys[0]['client_secret']})
            return jsonify(response)
    else:
        response = dict({'success': 'False', 'error': 'Wrong Username and Password'})
        return jsonify(response)

@oauth_bd.route('/fetch', methods=['POST'])
def fetch_credentials():
    """This API will fetch client ID/key if there exists at least one key/secret, or
    generate a new one if there are no ID/key"""
    cred = request.get_json()['data']
    email = cred['email']
    password = cred['password']
    user = User.objects(email=email).first()
    # TODO: disable change password for first login feature
    if user is not None and user.verify_password(password):
        creds = Client.objects(user=email)
        creds_size = len(creds)
        if creds_size > 0:
            creds = Client.objects(user=email)
            response = dict(responses.success_true)
            response.update({'client_id': creds[creds_size - 1]['client_id'],
                             'client_key': creds[creds_size - 1]['client_secret']})
            return jsonify(response)
        else:
            # generate new credentials
            keys = [{"client_id": gen_salt(40), "client_secret": gen_salt(50)}]
            item = Client(
                client_id=keys[0]['client_id'],
                client_secret=keys[0]['client_secret'],
                _redirect_uris=' '.join([
                    'http://localhost:8000/authorized',
                    'http://127.0.0.1:8000/authorized',
                    'http://127.0.1:8000/authorized',
                    'http://127.1:8000/authorized']),
                _default_scopes='email',
                user=email).save()
            response = dict(responses.success_true)
            response.update({'client_id': keys[0]['client_id'],
                             'client_key': keys[0]['client_secret']})
            return jsonify(response)
    else:
        response = dict({'success': 'False', 'error': 'Wrong Username and Password'})
        return jsonify(response)

@oauth_bd.route('/login', methods=['POST'])
def login_credentials():
    """This API will fetch client ID/key if there exists at least one key/secret, or
    generate a new one if there are no ID/key"""
    cred = request.get_json()['data']
    email = cred['email']
    password = cred['password']
    user = User.objects(email=email).first()
    if user is not None and user.verify_password(password):
        creds = Client.objects(user=email)
        creds_size = len(creds)
        if creds_size > 0:
            client = Client.objects(client_id=creds[creds_size - 1]['client_id'], client_secret=creds[creds_size - 1]['client_secret']).first()
            if client != None:
                # Set token expiry period and create it
                expires = datetime.utcnow() + timedelta(seconds=expires_in)
                tok = Token(
                             access_token=str(binascii.hexlify(os.urandom(16))),
                             refresh_token=str(binascii.hexlify(os.urandom(16))),
                             token_type='Bearer',
                             _scopes='email',
                             expires=expires,
                             client=client,
                             user=client.user,
                             email=client.user).save()
                response = dict(responses.success_true)
                response.update({'access_token': tok.access_token})
                return jsonify(response)
        else:
            # generate new credentials
            keys = [{"client_id": gen_salt(40), "client_secret": gen_salt(50)}]
            item = Client(
                client_id=keys[0]['client_id'],
                client_secret=keys[0]['client_secret'],
                _redirect_uris=' '.join([
                    'http://localhost:8000/authorized',
                    'http://127.0.0.1:8000/authorized',
                    'http://127.0.1:8000/authorized',
                    'http://127.1:8000/authorized']),
                _default_scopes='email',
                user=email).save()

            client = Client.objects(client_id=keys[0]['client_id'],
                                    client_secret=keys[0]['client_secret']).first()
            if client != None:
                # Set token expiry period and create it
                expires = datetime.utcnow() + timedelta(seconds=expires_in)
                tok = Token(
                    access_token=str(binascii.hexlify(os.urandom(16))),
                    refresh_token=str(binascii.hexlify(os.urandom(16))),
                    token_type='Bearer',
                    _scopes='email',
                    expires=expires,
                    client=client,
                    user=client.user,
                    email=client.user).save()
                response = dict(responses.success_true)
                response.update({'access_token': tok.access_token})
                return jsonify(response)
    else:
        response = dict({'success': 'False', 'error': 'Wrong Username and Password'})
        return jsonify(response)
