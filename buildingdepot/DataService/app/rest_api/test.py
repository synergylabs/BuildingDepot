from mongoengine import *
import redis

MONGODB_DATABASE = 'dataservice'
MONGODB_HOST = '127.0.0.1'
MONGODB_PORT = 27017

permissions_val = {"u/d":1,"r/w/p":2,"r/w":3,"r":4,"d/r":5}

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

connect(MONGODB_DATABASE,host=MONGODB_HOST,port=MONGODB_PORT)
register_connection('bd',name='buildingdepot',host='127.0.0.1',port=27017)

usergroup = "Synergy"
user_id = "tarun31@gmail.com"

r = redis.Redis()
pipe = r.pipeline()
permissions = Permission.objects(user_group=usergroup).first().update(permission="r/w/p")
