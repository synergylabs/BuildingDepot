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

    users = ListField(StringField())

    parents = ListField(EmbeddedDocumentField(Node))
    ancestors = ListField(EmbeddedDocumentField(Node))


class Building(Document):
    name = StringField(required=True, unique=True)
    template = StringField(required=True)
    description = StringField()

    metadata = DictField()

    tags = ListField(EmbeddedDocumentField(TagInstance))


class TagOwned(EmbeddedDocument):
    building = StringField()
    tags = ListField(EmbeddedDocumentField(Node))


class Role(Document):
    name = StringField(required=True, unique=True)
    description = StringField()
    permission = StringField(required='r')
    # super, local or default
    type = StringField(required=True, default='default')


class RolePerBuilding(EmbeddedDocument):
    role = StringField()
    building = StringField()


class User(UserMixin, Document):
    email = StringField(required=True, unique=True)
    password = StringField(required=True)
    name = StringField(required=True)

    role = ReferenceField(Role)
    # only used when the role type is default, indicate specific role in each building
    role_per_building = ListField(EmbeddedDocumentField(RolePerBuilding))
    buildings = ListField(StringField())
    tags_owned = ListField(EmbeddedDocumentField(TagOwned))

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




