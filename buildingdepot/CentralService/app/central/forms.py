"""
CentralService.form
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains the definitions for all the forms that will be shown to the user
in the frontend of the CentralService such as the form to create new buildings,
tags,dataserivces etc.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask.ext.wtf import Form
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
