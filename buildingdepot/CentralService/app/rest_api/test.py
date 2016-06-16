from mongoengine import *
import redis

MONGODB_DATABASE = 'buildingdepot'
MONGODB_HOST = '127.0.0.1'
MONGODB_PORT = 27017

permissions_val = {"u/d": 1, "r/w/p": 2, "r/w": 3, "r": 4, "d/r": 5}


class Node(EmbeddedDocument):
    name = StringField()
    value = StringField()


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


class UserGroup(Document):
    name = StringField(required=True, unique=True)
    description = StringField()

    users = ListField(StringField())


class Permission(Document):
    user_group = StringField()
    sensor_group = StringField()
    permission = StringField()


class TagInstance(EmbeddedDocument):
    name = StringField()
    value = StringField()

    metadata = DictField()
    parents = ListField(EmbeddedDocumentField(Node))
    acl_tag = BooleanField()


class Building(Document):
    name = StringField(required=True, unique=True)
    template = StringField(required=True)
    description = StringField()

    metadata = DictField()

    tags = ListField(EmbeddedDocumentField(TagInstance))


class DataService(Document):
    name = StringField(required=True, unique=True)
    description = StringField()

    host = StringField(required=True)
    port = IntField(required=True)

    buildings = ListField(StringField())

    admins = ListField(StringField())


connect(MONGODB_DATABASE, host=MONGODB_HOST, port=MONGODB_PORT)
register_connection('bd', name='buildingdepot', host='127.0.0.1', port=27017)

usergroup = "Synergy"
user_id = "tarun31@gmail.com"

r = redis.Redis()
pipe = r.pipeline()
collection = DataService._get_collection()
ds = collection.find({"buildings": "Wean"})
print ds[0]['admins']
