"""
DataService.form
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains the definitions for all the forms that will be shown to the user
in the frontend of the DataService.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask.ext.wtf import Form
from wtforms import StringField, SelectMultipleField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired


class SensorForm(Form):
    source_name = StringField('Source Name')
    source_identifier = StringField('Source Identifier')
    Type = StringField('BrickTypeOfObject') #Change
    building = SelectField('Building', validators=[DataRequired()])
    submit = SubmitField('Submit')


class PermissionQueryForm(Form):
    user = StringField('User Email', validators=[DataRequired()])
    sensor = StringField('Sensor ID', validators=[DataRequired()])
    submit = SubmitField('Submit')
