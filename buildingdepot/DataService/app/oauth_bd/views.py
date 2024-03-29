"""
DataService.oauth_bd.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains all the class and method definitions required for the OAuth
token generation and verification

@copyright: (c) 2024 SynergyLabs
@license: CMU License. See License file for details.
"""

import binascii
import os
import sys
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from flask import Flask, current_app, Blueprint
from flask import render_template, redirect, jsonify
from flask import session, request
from flask_oauthlib.client import OAuth
from mongoengine import *
from mongoengine.context_managers import switch_db
from uuid import uuid4
from werkzeug.security import gen_salt
from xmlrpc.client import ServerProxy

from . import oauth_bd
from .. import oauth, r
from ..service.utils import get_user_oauth

expires_in = 34560


class Client(Document):
    client_id = StringField(required=True, unique=True)
    client_secret = StringField(required=True)
    user = StringField()
    _redirect_uris = StringField()
    _default_scopes = StringField()

    @property
    def client_type(self):
        return "public"

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


def current_user():
    if "email" in session:
        email = session["email"]
        return get_user_oauth(email)
    return None


@oauth_bd.route("/", methods=("GET", "POST"))
def home():
    if request.method == "POST":
        email = request.form.get("username")
        user = get_user_oauth(email)
        if not user:
            return jsonify({"response": "Access Denied"})
        session["email"] = user
        return redirect("/")
    user_current = current_user()
    return render_template("home.html", user=user_current)


@oauth_bd.route("/client")
def client():
    user_current = current_user()
    if not user_current:
        return redirect("/")
    item = Client(
        client_id=gen_salt(40),
        client_secret=gen_salt(50),
        _redirect_uris=" ".join(
            [
                "http://localhost:8000/authorized",
                "http://127.0.0.1:8000/authorized",
                "http://127.0.1:8000/authorized",
                "http://127.1:8000/authorized",
            ]
        ),
        _default_scopes="email",
        user=get_user_oauth(user_current),
    ).save()
    return jsonify(client_id=item.client_id, client_secret=item.client_secret)


@oauth.clientgetter
def load_client(client_id):
    return Client.objects(client_id=client_id).first()


@oauth.grantgetter
def load_grant(client_id, code):
    return Grant.objects(
        client=Client.objects(client_id=client_id).first(), code=code
    ).first()


@oauth.grantsetter
def save_grant(client_id, code, request, *args, **kwargs):
    expires = datetime.utcnow() + timedelta(seconds=100)
    grant = Grant(
        client=Client.objects(client_id=client_id).first(),
        code=code["code"],
        redirect_uri=request.redirect_uri,
        _scopes=" ".join(request.scopes),
        user=get_user_oauth(current_user()),
        expires=expires,
    )
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
    previous_tokens = ["oauth"]
    for t in toks:
        previous_tokens.append("".join(["oauth:", t.access_token]))
        t.delete()
    r.delete(*previous_tokens)
    expires_in = token.pop("expires_in")
    expires = datetime.utcnow() + timedelta(seconds=expires_in)
    tok = Token(
        access_token=token["access_token"],
        refresh_token=token["refresh_token"],
        token_type=token["token_type"],
        _scopes=token["scope"],
        expires=expires,
        client=request.client,
        user=request.user,
        email=request.user,
    ).save()
    r.setex("".join(["oauth:", tok.access_token]), expires_in, client.user)
    return tok


@oauth_bd.route(
    "/access_token/client_id=<client_id>/client_secret=<client_secret>", methods=["GET"]
)
def get_access_token(client_id, client_secret):
    """Generates and returns an access token to the user if the client_id and
    client_secret provided by them are valid"""
    client = Client.objects(client_id=client_id, client_secret=client_secret).first()
    if client != None:
        # Set token expiry period and create it
        expires = datetime.utcnow() + timedelta(seconds=expires_in)
        tok = Token(
            access_token=str(binascii.hexlify(os.urandom(16))),
            refresh_token=str(binascii.hexlify(os.urandom(16))),
            token_type="Bearer",
            _scopes="email",
            expires=expires,
            client=client,
            user=client.user,
            email=client.user,
        ).save()
        r.setex("".join(["oauth:", tok.access_token]), expires_in, client.user)
        return jsonify({"success": "True", "access_token": tok.access_token})
    return jsonify({"success": "False", "access_token": "Invalid credentials"})
