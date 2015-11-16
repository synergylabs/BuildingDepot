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

class Client(Document):
    client_id = StringField(required=True, unique=True)
    client_secret = StringField(required=True)
    user = StringField()
    _redirect_uris = StringField()
    _default_scopes = StringField()

    @property
    def client_type(self):
        return 'public'

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0]

    @property
    def default_scopes(self):
        if self._default_scopes:
            return self._default_scopes.split()
        return []


