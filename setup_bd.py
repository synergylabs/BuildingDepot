#!/srv/buildingdepot/venv/bin/python
import configparser
import io
import json
import os
import random
import string
import sys
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

print("Setting up BuildingDepot.. ")

option = sys.argv[1:][0]  # get arguments

# Create a temporary password
tempPwd = "".join(
    random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase)
    for _ in range(16)
)

# Get Username and Password for MongoDB
if option == "install":
    configBuffer = io.StringIO()
    configBuffer.write("[dummysection]\n")
    configBuffer.write(open("/srv/buildingdepot/CentralService/cs_config").read())
    configBuffer.seek(0, os.SEEK_SET)
    config = configparser.ConfigParser()
    config.read_file(configBuffer)
    user = config.get("dummysection", "MONGODB_USERNAME").strip("'").strip('"')
    pwd = config.get("dummysection", "MONGODB_PWD").strip("'").strip('"')

elif option == "bd_install":
    configs = json.load(open("configs/bd_config.json", "r"))
    user = configs["mongo_user"]
    pwd = configs["mongo_pwd"]

elif option == "test":
    configBuffer = io.StringIO()
    configBuffer.write("[dummysection]\n")
    configBuffer.write(open("/srv/buildingdepot/CentralService/cs_config").read())
    configBuffer.seek(0, os.SEEK_SET)
    config = configparser.ConfigParser()
    config.read_file(configBuffer)
    user = config.get("dummysection", "MONGODB_USERNAME").strip("'").strip('"')
    pwd = config.get("dummysection", "MONGODB_PWD").strip("'").strip('"')
    configs = json.load(
        open("benchmarking-tools/functional-testing-tool/tests/config.json", "r")
    )
    test_config = dict(configs)
    test_config["password"] = tempPwd
    with open(
        "benchmarking-tools/functional-testing-tool/tests/config.json", "w"
    ) as output:
        json.dump(test_config, output)

else:
    exit(0)

# Create BuildingDepot Database
client = MongoClient(username=user, password=pwd, authSource="admin")
db = client.buildingdepot
db.user.insert_one(
    {
        "email": "admin@buildingdepot.org",
        "password": generate_password_hash(tempPwd),
        "first_name": "Admin",
        "first_login": True,
        "role": "super",
    }
)
db.data_service.insert_one(
    {
        "name": "ds1",
        "description": "",
        "host": "127.0.0.1",
        "port": 82,
        "buildings": [],
        "admins": [],
    }
)

print(
    (
        "\n Created a super user with following credentials. Please login and change password immediately \n user id "
        ": admin@buildingdepot.org \n password: " + tempPwd
    )
)
