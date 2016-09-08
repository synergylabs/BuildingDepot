"""
CentralReplica.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Replicates all the models that are defined in the CentralService
as the CentralReplica needs them for it's RPC's.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""


from mongoengine import *
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import check_password_hash
from config import Config


"""
CentralService.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains all the class definitions that are required for the CentralService.
Each class here is a Table in MongoDB where each value that is inserted into
these tables can have any of the paramteres defined within the class

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask import current_app
from mongoengine import *
from flask.ext.login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash


class DataService(Document):
    name = StringField(required=True, unique=True)
    description = StringField()

    host = StringField(required=True)
    port = IntField(required=True)

    buildings = ListField(StringField())

    admins = ListField(StringField())


class TagType(Document):
    name = StringField(required=True, unique=True)
    description = StringField()

    parents = ListField(StringField())
    children = ListField(StringField())
    acl_tag = BooleanField()


class BuildingTemplate(Document):
    name = StringField(required=True, unique=True)
    description = StringField()

    tag_types = ListField(StringField())


class Node(EmbeddedDocument):
    name = StringField()
    value = StringField()


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


class TagOwned(EmbeddedDocument):
    building = StringField()
    tags = ListField(EmbeddedDocumentField(Node))

class User(Document):
    email = StringField(required=True, unique=True)
    password = StringField(required=True)
    first_name = StringField(required=True)
    last_name = StringField()
    role = StringField()
    first_login = BooleanField(default=False)

    def get_id(self):
        return self.email

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'email': self.email})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None

        return User.objects(email=data['email']).first()

    def is_super(self):
        return self.role.type == 'super'

    def is_local(self):
        return self.role.type == 'local'

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




