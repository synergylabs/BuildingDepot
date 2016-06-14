"""
DataService.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains all the class definitions that are required for the DataService.
Each class here is a Table in MongoDB where each value that is inserted into
these tables can have any of the paramteres defined within the class

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from mongoengine import *


class Node(EmbeddedDocument):
    name = StringField()
    value = StringField()

    meta = {"db_alias": "ds"}

class UserGroupNode(EmbeddedDocument):
    user_id = StringField()
    manager = BooleanField()

    meta = {"db_alias": "ds"}

class Sensor(Document):
    name = StringField(required=True, unique=True)
    source_name = StringField()
    source_identifier = StringField()
    owner = StringField()

    metadata = DictField()
    building = StringField()
    tags = ListField(EmbeddedDocumentField(Node))
    subscribers = ListField(StringField())

    meta = {"db_alias": "ds"}


class SensorGroup(Document):
    name = StringField(required=True, unique=True)
    description = StringField()

    building = StringField()
    tags = ListField(EmbeddedDocumentField(Node))
    owner = StringField()

    meta = {"db_alias": "ds"}

class UserGroup(Document):
    name = StringField(required=True, unique=True)
    description = StringField()
    owner = StringField()

    users = ListField(EmbeddedDocumentField(UserGroupNode))

    meta = {"db_alias": "ds"}


class Permission(Document):
    user_group = StringField()
    sensor_group = StringField()
    permission = StringField()
    owner = StringField()

    meta = {"db_alias": "ds"}


class Application(Document):
    user = StringField()
    apps = ListField(EmbeddedDocumentField(Node))

    meta = {"db_alias": "ds"}
