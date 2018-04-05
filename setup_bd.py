#!/srv/buildingdepot/venv/bin/python2.7

from pymongo import MongoClient
from werkzeug.security import generate_password_hash

client = MongoClient()
db = client.buildingdepot
db.user.create_index('email')
db.user.insert({"email":"admin@buildingdepot.org",
                "password":generate_password_hash("admin"),
                "first_name":"Admin",
                "first_login":True,
                "role":"super"})
db.data_service.insert({'name':'ds1',
                        'description':'',
                        'host':'127.0.0.1',
                        'port':82,
                        'buildings':[],
                        'admins':[]})
