"""
DataService.auth.forms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Class definition for the login form

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""
from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email


class LoginForm(Form):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

