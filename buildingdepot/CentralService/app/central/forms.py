"""
CentralService.form
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains the definitions for all the forms that will be shown to the user
in the frontend of the CentralService such as the form to create new buildings,
tags,dataserivces etc.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask_wtf import Form
from wtforms import StringField, SelectMultipleField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired


class TagTypeForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')
    parents = SelectMultipleField('Parents')
    submit = SubmitField('Submit')


class BuildingTemplateForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')
    tag_types = SelectMultipleField('Tag types')
    submit = SubmitField('Submit')


class BuildingForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')
    template = SelectField('Template', validators=[DataRequired()])
    submit = SubmitField('Submit')


class RoleForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')
    permission = SelectField('Permission', choices=[('r', 'r'), ('r/w', 'r/w')], validators=[DataRequired()])
    type = SelectField('Type',
                       choices=[('default', 'default'), ('local', 'local'), ('super', 'super')],
                       validators=[DataRequired()])
    submit = SubmitField('Submit')


class DataServiceForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')
    host = StringField('Host', validators=[DataRequired()])
    port = StringField('Port', validators=[DataRequired()])
    submit = SubmitField('Submit')

class SensorForm(Form):
    source_name = StringField('Source Name')
    source_identifier = StringField('Source Identifier')
    building = SelectField('Building', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SensorGroupForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')
    building = SelectField('Building', validators=[DataRequired()])
    submit = SubmitField('Submit')


class UserGroupForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')
    submit = SubmitField('Submit')


class PermissionForm(Form):
    user_group = SelectField('User Group', validators=[DataRequired()])
    sensor_group = SelectField('Sensor Group', validators=[DataRequired()])
    permission = SelectField('Building', choices=[('r', 'r'),('r/w', 'r/w'),('d/r','d/r'),('r/w/p', 'r/w/p')], validators=[DataRequired()])
    submit = SubmitField('Submit')


class PermissionQueryForm(Form):
    user = StringField('User Email', validators=[DataRequired()])
    sensor = StringField('Sensor ID', validators=[DataRequired()])
    submit = SubmitField('Submit')
