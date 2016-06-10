"""
CentalService.auth.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains all the definitions for the CentralService authroization functions.
The functionalities available are for registering a new user,logging in and
logging out.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask import render_template, redirect, request
from flask import session, url_for, flash
from . import auth
from flask.ext.login import login_user, login_required, logout_user
from ..models.cs_models import User
from .forms import LoginForm, RegistrationForm
from werkzeug.security import generate_password_hash


@auth.route('/register', methods=['GET', 'POST'])
def register():
    "Register a new user"
    form = RegistrationForm()
    if form.validate_on_submit():
        """Create a new user"""
        User(email=form.email.data,
             name=form.name.data,
             password=generate_password_hash(form.password.data)).save()
        flash('You can now login.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Login a user if credentials are valid"""
    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        session['email'] = form.email.data
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid email or password')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    """ Logout user"""
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('main.index'))