from cs_models import *
from mongoengine import connect

connect('buildingdepot')

Role.drop_collection()
User.drop_collection()
role = Role(name='super', type='super', permission=True, description='').save()
print role
user = User(email='admin@gmail.com', name='jimmy', password='123', role=role).save()
print user


# import requests
# import json
# from requests.auth import HTTPBasicAuth
# url = 'http://127.0.0.1:5000/api/v0.0/buildingtemplates?page=2'
# auth = HTTPBasicAuth('admin@gmail.com', '123')
# payload = {'name': 'CSE', 'template': 't1', 'description': 'Basic', 'metadata': {'length': 1}}
# # print requests.post(url, auth=auth, json=payload).content
#
#
# url = 'http://127.0.0.1:5000/api/v0.0/tagtypes/area3'
# # print requests.delete(url, auth=auth).content
#
# url = 'http://127.0.0.1:5000/api/v0.0/buildings'
# print requests.post(url, auth=auth, json=payload).content

# import requests
# import json
# from requests.auth import HTTPBasicAuth
# auth = HTTPBasicAuth('admin@gmail.com', '123')
# url = 'http://127.0.0.1:5000/api/v0.0/buildings/CSE/tags'
# payload = {'name': 'area1', 'value': '123', 'description': 'Basic', 'metadata': {'length': 1}, 'parents': {'name': 1, 'value': 2}}
# print requests.post(url, auth=auth, json=payload).content