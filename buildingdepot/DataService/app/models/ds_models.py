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

class UserGroupNode(EmbeddedDocument):
    user_id = StringField()
    manager = BooleanField()

class Sensor(Document):
    name = StringField(required=True, unique=True)
    source_name = StringField()
    source_identifier = StringField()
    owner = StringField()
    Enttype = StringField() #
    timeseries = StringField()
   
    metadata = DictField()
    building = StringField()
    tags = ListField(EmbeddedDocumentField(Node))
    subscribers = ListField(StringField())

class BrickType(Document): #
    name = StringField(required=True,unique=True)#
    subClass = ListField(StringField()) #
    SuperClass = ListField(StringField()) #
    equivalentClass = ListField(StringField()) #
    Domain = ListField(StringField()) #
    Type = ListField(StringField())
    InverseOf = ListField(StringField())
    OnProperty = ListField(StringField())
    Range = ListField(StringField())
    SubPropertyOf = ListField(StringField())
    SuperPropertyOf = ListField(StringField())
    SomeValuesFrom = ListField(StringField())
    UsesTag = ListField(StringField())
    Label = ListField(StringField())
    Imports = ListField(StringField())
    Comment = ListField(StringField())
    isHierarchical = ListField(StringField())

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
