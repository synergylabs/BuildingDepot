import requests
from requests.auth import HTTPBasicAuth
from cs_models import *
from mongoengine import connect

connect('buildingdepot')
auth = HTTPBasicAuth('synergy@gmail.com', 'synergy469321')



def post_tag_types(payload):
    url = 'http://127.0.0.1:81/api/v0.0/tagtypes'
    requests.post(url, auth=auth, json=payload)


def post_building_templates(payload):
    url = 'http://127.0.0.1:81/api/v0.0/buildingtemplates'
    requests.post(url, auth=auth, json=payload)


def post_building(payload):
    url = 'http://127.0.0.1:81/api/v0.0/buildings'
    requests.post(url, auth=auth, json=payload)


def post_building_tags(payload):
    url = 'http://127.0.0.1:81/api/v0.0/buildings/ECE/tags'
    print requests.post(url, auth=auth, json=payload).content


def get_building():
    url = 'http://127.0.0.1:81/api/v0.0/buildings'
    print requests.get(url, auth=auth).content


def delete_building():
    url = 'http://127.0.0.1:81/api/v0.0/buildings/ECE'
    print requests.delete(url, auth=auth).content


def preprocess():
    TagType.drop_collection()
    BuildingTemplate.drop_collection()
    Building.drop_collection()

    payload = {'name': 'zone'}
    post_tag_types(payload)
    payload = {'name': 'floor', 'parents': 'zone'}
    post_tag_types(payload)
    payload = {'name': 'room', 'parents': 'floor'}
    post_tag_types(payload)

    payload = {'name': 'basic', 'tag_types': ['zone', 'floor', 'room']}
    post_building_templates(payload)

    payload = {'name': 'ECE', 'template': 'basic'}
    post_building(payload)


def test_building_tag_post():
    payload = {'name': 'floor', 'value': '2'}
    post_building_tags(payload)
    payload = {'name': 'room', 'value': '3', 'parents': {'name': 'floor', 'value': 2}}
    post_building_tags(payload)

# post_building({'name': 'Bio', 'template': 'basic', 'metadata': {'l': 1, 'a': 2}})


def get_building_tags():
    url = 'http://127.0.0.1:81/api/v0.0/buildings/ECE/tags'
    print requests.get(url, auth=auth).content


def post_role(payload):
    url = 'http://127.0.0.1:81/api/v0.0/roles'
    print requests.post(url, auth=auth, json=payload).content

# payload = {'name': 'local', 'permission': True, 'type': 'local'}
# post_role(payload)

# def post_user():
#     url = 'http://127.0.0.1:81/api/v0.0/users'
#     payload = {
#         'email': 'zhp2@gmail.com',
#         'password': '1234567',
#         'name': 'jj',
#         'role': 'local'
#     }
#     print requests.post(url, auth=auth, json=payload).content
#
# post_user()

# def post_local_user_buildings():
#     url = 'http://127.0.0.1:81/api/v0.0/users/zhp2@gmail.com/buildings'
#     payload = {
#         'buildings': ['ECE']
#     }
#     print requests.post(url, auth=auth, json=payload).content
#
# post_local_user_buildings()

def post_default_user_tags_owned():
    url = 'http://127.0.0.1:81/api/v0.0/users/zhp@gmail.com/tags_owned'
    payload = {
        'tags_owned': [{'building': 'CSE', 'tags': [{'name': 'floor', 'value': '1'}]}]
    }
    print requests.post(url, auth=auth, json=payload).content

def post_building_tag_metadata():
    url = 'http://127.0.0.1:81/api/v0.0/buildings/ECE/tags/floor/2/metadata'
    payload = {
        'metadata': {
            'ko': 'a'
        }
    }
    print requests.post(url, auth=auth, json=payload).content

get_building_tags()
#post_building_tag_metadata()
#post_default_user_tags_owned()
