"""
DataService.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains all the class definitions that are required for the DataService.
Each class here is a Table in MongoDB where each value that is inserted into
these tables can have any of the paramteres defined within the class

@copyright: (c) 2020 SynergyLabs
@license: CMU License. See License file for details.
"""

from mongoengine import *


class Node(EmbeddedDocument):
    name = StringField()
    value = StringField()


class UserGroupNode(EmbeddedDocument):
    user_id = StringField()
    manager = BooleanField()


class User(Document):
    email = StringField(required=True, unique=True)
    password = StringField(required=True)
    first_name = StringField(required=True)
    last_name = StringField()
    role = StringField()
    first_login = BooleanField(default=True)

    def get_id(self):
        return self.email

    def is_super(self):
        return self.role.type == "super"

    def is_default(self):
        return self.role.type == "default"


class Sensor(Document):
    name = StringField(required=True, unique=True)
    source_name = StringField()
    source_identifier = StringField()
    owner = StringField()

    metadata = DictField()
    building = StringField()
    tags = ListField(EmbeddedDocumentField(Node))
    subscribers = ListField(StringField())


class SensorGroup(Document):
    name = StringField(required=True, unique=True)
    description = StringField()

    building = StringField()
    tags = ListField(EmbeddedDocumentField(Node))
    owner = StringField()


class UserGroup(Document):
    name = StringField(required=True, unique=True)
    description = StringField()
    owner = StringField()

    users = ListField(EmbeddedDocumentField(UserGroupNode))


class Permission(Document):
    user_group = StringField()
    sensor_group = StringField()
    permission = StringField()
    owner = StringField()


class Application(Document):
    user = StringField()
    apps = ListField(EmbeddedDocumentField(Node))


class TagType(Document):
    name = StringField(required=True, unique=True)
    description = StringField()
    parents = ListField(StringField())
    children = ListField(StringField())
    acl_tag = BooleanField()


class TagInstance(EmbeddedDocument):
    name = StringField()
    value = StringField()
    metadata = DictField()
    parents = ListField(EmbeddedDocumentField(Node))


class Building(Document):
    name = StringField(required=True, unique=True)
    template = StringField(required=True)
    description = StringField()
    metadata = DictField()
    tags = ListField(EmbeddedDocumentField(TagInstance))
