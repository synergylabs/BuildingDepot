"""
DataService.auth.forms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Class definition for the login form

@copyright: (c) 2021 SynergyLabs
@license: CMU License. See License file for details.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")
