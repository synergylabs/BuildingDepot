"""
DataService.auth.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Functions for user login and logout from the DataService

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

import binascii
import os
from datetime import datetime, timedelta

from flask import render_template, redirect, url_for, flash, session, make_response
from werkzeug.security import gen_salt

from . import auth
from .forms import LoginForm
from .. import svr
from ..models.ds_models import *


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


def token_gen(client_id, client_secret):
    client = Client.objects(client_id=client_id, client_secret=client_secret).first()
    if client is not None:
        toks = Token.objects(user=client.user)
        for t in toks:
            t.delete()
        # Set token expiry period and create it
        expires_in = 864000
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
    return tok.access_token


def oauth_gen(email):
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
    token = token_gen(keys[0]['client_id'], keys[0]['client_secret'])
    return token


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    keys = []
    if form.validate_on_submit():
        if svr.get_user(form.email.data, form.password.data):
            session['email'] = form.email.data
            if len(Client.objects(user=session['email'])) > 0:
                clientkeys = Client.objects(user=session['email']).first()
                token = token_gen(clientkeys.client_id, clientkeys.client_secret)
            else:
                token = oauth_gen(form.email.data)
            resp = make_response(redirect(url_for('service.sensor')))
            resp.set_cookie('access_token', value=token)
            return resp
        flash('Invalid email or password!')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
def logout():
    session.pop('email', None)
    resp = make_response(redirect(url_for('main.index')))
    resp.set_cookie('access_token', value='', expires=0)
    flash('You have been logged out!')
    return resp
