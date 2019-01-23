#!/srv/buildingdepot/venv/bin/python2.7
import json,sys
import StringIO,os,ConfigParser
import string,random
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

print "Setting up BuildingDepot.. "

option = sys.argv[1:][0] #get arguments

# Get Username and Password for MongoDB
if (option == "install"):
    configBuffer = StringIO.StringIO()
    configBuffer.write('[dummysection]\n')
    configBuffer.write(open('/srv/buildingdepot/CentralService/cs_config').read())
    configBuffer.seek(0, os.SEEK_SET)
    config = ConfigParser.ConfigParser()
    config.readfp(configBuffer)
    user=config.get('dummysection','MONGODB_USERNAME').strip("'").strip('"')
    pwd = config.get('dummysection','MONGODB_PWD').strip("'").strip('"')

elif(option == "bd_install"):
    configs = json.load(open('configs/bd_config.json', 'r'))
    user = configs['mongo_user']
    pwd = configs['mongo_pwd']

else:
    exit(0)

#Create BuildingDepot Database
client = MongoClient(username=user,
                     password=pwd,
                     authSource='admin')
db = client.buildingdepot
tempPwd = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(16))
db.user.insert({"email":"admin@buildingdepot.org",
                "password":generate_password_hash(tempPwd),
                "first_name":"Admin",
                "first_login":True,
                "role":"super"})
db.data_service.insert({'name':'ds1',
                        'description':'',
                        'host':'127.0.0.1',
                        'port':82,
                        'buildings':[],
                        'admins':[]})

print "\n Created a super user with following credentials. Please login and change password immediately \n user id "\
      ": admin@buildingdepot.org \n password: " + tempPwd
