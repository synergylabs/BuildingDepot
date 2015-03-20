import requests
from requests.auth import HTTPBasicAuth

from mongoengine import *
# connect('dataservice',
#         host='127.0.0.1',
#         port=27020)

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


auth = HTTPBasicAuth('zhp@gmail.com', '1')


def get_subscription():
    url = 'http://127.0.0.1:5001/api/v0.0/subscription/rr@gmail.com'
    print requests.get(url).content


def post_subscription(payload):
    url = 'http://127.0.0.1:5001/api/v0.0/subscription/rr@gmail.com'
    print requests.post(url, json=payload, auth=auth).content


def get_timeseries():
    url = 'http://127.0.0.1:5001/api/v0.0/sensor/ad984bcb-4303-45c4-a844-7374279dbc0b/timeseries?start=31536000'
    print requests.get(url, auth=auth).content


def get_change():
    url = 'http://127.0.0.1:5001/api/v0.0/subscription/rr@gmail.com/changes'
    print requests.get(url).content


def clear_change():
    url = 'http://127.0.0.1:5001/api/v0.0/subscription/rr@gmail.com/clearchanges/e9ea8afe-cdf8-4a2a-b10d-dc17fde7afa2'
    print requests.post(url).content

def get_token():
    url = 'http://127.0.0.1:5001/api/v0.0/token'
    print requests.get(url, auth=auth).content


def search(payload):
    url = 'http://127.0.0.1:5001/api/v0.0/search/sensors'
    print requests.get(url, auth=auth, json=payload).content


def post_timeseries(payload):
    url = 'http://127.0.0.1:5001/api/v0.0/sensor/31d3ed97-1575-4759-98ab-45b3902b6ac7/timeseries'
    print requests.post(url, json=payload, auth=auth).content


def read_page():
    url = 'http://127.0.0.1:5001/service/sensor'
    requests.get(url)

import time
import urllib2
s = time.time()
# post_timeseries({'timeseries': [{'2134': 45}]})
read_page()
e = time.time()
print e-s

s = time.time()
urllib2.urlopen('http://127.0.0.1:5001/service/sensor')
e = time.time()
print e-s
