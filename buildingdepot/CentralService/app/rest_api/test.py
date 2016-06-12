from mongoengine import *
import redis

MONGODB_DATABASE = 'buildingdepot'
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

class DataService(Document):
    name = StringField(required=True, unique=True)
    description = StringField()

    host = StringField(required=True)
    port = IntField(required=True)

    buildings = ListField(StringField())

    admins = ListField(StringField())

connect(MONGODB_DATABASE,host=MONGODB_HOST,port=MONGODB_PORT)
register_connection('bd',name='buildingdepot',host='127.0.0.1',port=27017)

usergroup = "Synergy"
user_id = "tarun31@gmail.com"

r = redis.Redis()
pipe = r.pipeline()
tags_list = [{"name":"Floor","value":"3"}]
#collection = Building._get_collection()
#print collection.find({"tags":tags_list}).count()
#buildings = collection.find({"tags.value": {"$all":["3","3500"]},"tags.name": {"$all":["Floor"]}})
#buildings = collection.find({"tags":{"$in":[{"name":"Floor","value":"3"}]}})
#buildings = collection.find({"tags.parents":{"$elemMatch":{"name":"Floor","value":"3"}}})
#buildings = Building._get_collection().find({'tags':{"$elemMatch":{"name":"Floor","value":"4"}}})
#print buildings.count()
#for building in buildings:
#	print building['name']
#collection.update({'name':"Wean"},{'$pull':{'tags':{'name':"Floor",'value':"3"}}})
#tag_exists = collection.update({'name':'Wean','tags':{"$elemMatch":{"name":"Floor","value":"3"}}},{"$unset":{"parents":""},"$push":{"tags.$.parents":{"$each":[{"name":"Floor","value":"6"},{"name":"Floor","value":"7"}]}}})
collection = DataService._get_collection()
collection.update({'name':"ds2"},{'$pullAll':{'buildings':['Wean','NSH']}})
