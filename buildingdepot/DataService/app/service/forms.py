"""
DataService.form
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains the definitions for all the forms that will be shown to the user
in the frontend of the DataService.

@copyright: (c) 2024 SynergyLabs
@license: CMU License. See License file for details.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectMultipleField,
    SubmitField,
    SelectField,
    BooleanField,
)
from wtforms.validators import DataRequired


class SensorForm(FlaskForm):
    source_name = StringField("Source Name")
    source_identifier = StringField("Source Identifier")
    building = SelectField("Building", validators=[DataRequired()])
    submit = SubmitField("Submit")


class PermissionQueryForm(FlaskForm):
    user = StringField("User Email", validators=[DataRequired()])
    sensor = StringField("Sensor ID", validators=[DataRequired()])
    submit = SubmitField("Submit")
