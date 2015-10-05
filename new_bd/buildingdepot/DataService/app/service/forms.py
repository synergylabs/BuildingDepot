from flask.ext.wtf import Form
from wtforms import StringField, SelectMultipleField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired


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
    permission = SelectField('Building', choices=[('r', 'r'), ('r/w', 'r/w')], validators=[DataRequired()])
    submit = SubmitField('Submit')


class PermissionQueryForm(Form):
    user = StringField('User Email', validators=[DataRequired()])
    sensor = StringField('Sensor ID', validators=[DataRequired()])
    submit = SubmitField('Submit')