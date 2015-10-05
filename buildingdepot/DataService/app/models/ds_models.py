from mongoengine import *


class Node(EmbeddedDocument):
    name = StringField()
    value = StringField()


class Sensor(Document):
    name = StringField(required=True, unique=True)
    source_name = StringField()
    source_identifier = StringField()

    metadata = DictField()
    building = StringField()
    tags = ListField(EmbeddedDocumentField(Node))


class SensorGroup(Document):
    name = StringField(required=True, unique=True)
    description = StringField()

    building = StringField()
    tags = ListField(EmbeddedDocumentField(Node))


class UserGroup(Document):
    name = StringField(required=True, unique=True)
    description = StringField()

    users = ListField(StringField())


class Permission(Document):
    user_group = StringField()
    sensor_group = StringField()
    permission = StringField()
