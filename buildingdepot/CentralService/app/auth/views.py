"""
CentalService.auth.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains all the definitions for the CentralService authroization functions.
The functionalities available are for registering a new user,logging in and
logging out.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

import sys, os, binascii
from flask import render_template, redirect, request
from flask import session, url_for, flash, make_response
from . import auth
from datetime import datetime, timedelta
from flask_login import login_user, login_required, logout_user
from .forms import LoginForm, RegistrationForm
from ..models.cs_models import *
from werkzeug.security import generate_password_hash, gen_salt
from .. import r


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
        toks = Token.objects(client=client)
        previous_tokens = ["oauth"]
        for t in toks:
            previous_tokens.append("".join(["oauth:", t.access_token]))
            t.delete()
        r.delete(*previous_tokens)
        # Set token expiry period and create it
        expires_in = 864000
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
    r.setex("".join(["oauth:", tok.access_token]), client.user, expires_in)
    return tok.access_token


def oauth_gen(email):
    keys = [{"client_id": gen_salt(40), "client_secret": gen_salt(50)}]
    item = Client(
        client_id=keys[0]["client_id"],
        client_secret=keys[0]["client_secret"],
        _redirect_uris=" ".join(
            [
                "http://localhost:8000/authorized",
                "http://127.0.0.1:8000/authorized",
                "http://127.0.1:8000/authorized",
                "http://127.1:8000/authorized",
            ]
        ),
        _default_scopes="email",
        user=email,
    ).save()
    token = token_gen(keys[0]["client_id"], keys[0]["client_secret"])
    return token


@auth.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user"""
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.objects(email=session["email"]).first()
        if user.update(
            set__password=generate_password_hash(form.password.data),
            set__first_login=False,
        ):
            flash("Your Password is successfully reset. You can now login.")
            return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth.route("/login", methods=["GET", "POST"])
def login():
    """Login a user if credentials are valid"""
    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if (
            user is not None
            and user.first_login
            and user.verify_password(form.password.data)
        ):
            flash("You have logged in for the first time. Create a new password")
            session["email"] = form.email.data
            return redirect(url_for("auth.register"))
        elif user is not None and user.verify_password(form.password.data):
            if len(Client.objects(user=form.email.data)) > 0:
                clientkeys = Client.objects(user=form.email.data).first()
                token = token_gen(clientkeys.client_id, clientkeys.client_secret)
            else:
                token = oauth_gen(form.email.data)
            login_user(user, form.remember_me.data)
            session["email"] = form.email.data
            session["token"] = token
            session["headers"] = {
                "Authorization": "Bearer " + session["token"],
                "Content-Type": "application/json",
            }
            resp = make_response(redirect(url_for("central.sensor")))
            resp.set_cookie("access_token", value=token)
            return resp
            # return redirect(request.args.get('next') or url_for('main.index'))
        flash("Invalid email or password")
    return render_template("auth/login.html", form=form)


@auth.route("/logout")
@login_required
def logout():
    """ Logout user"""
    logout_user()
    flash("You have been logged out")
    return redirect(url_for("main.index"))
