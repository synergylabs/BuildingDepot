"""
CentalService.auth.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains all the forms for the CentralService authorization functions.
The two forms that are used are for login and for creating a new user.

@copyright: (c) 2024 SynergyLabs
@license: CMU License. See License file for details.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Email, Length, EqualTo

from ..models.cs_models import User


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Keep me logged in")
    submit = SubmitField("Log In")


class RegistrationForm(FlaskForm):
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            EqualTo("password2", message="Passwords must match"),
        ],
    )
    password2 = PasswordField("Confirm password", validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_email(self, field):
        if User.objects(email=field.data).first() is not None:
            raise ValidationError("Email already registered.")
