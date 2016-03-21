import sys, os, thread, requests, json, time, random, threading, datetime
from pprint import pprint

def getOauthToken(cid, ckey):
  url = baseUrl+"/oauth/access_token/client_id="+cid+"/client_secret="+ckey
  response = requests.get(url).json()
  access_token = response["access_token"]
  return access_token

def list_sensor(cid, ckey):
  OauthToken = getOauthToken(cid, ckey)
  url = baseUrl+"/api/list"
  header = {"Authorization": "bearer " + OauthToken}
    
  try:
    response = requests.get(url, headers = header).json()
  except Exception as e:
    print "Invalid json in list_sensor" 
    return {}

  return response

def list_by_tag(param, value, cid, ckey):
  OauthToken = getOauthToken(cid, ckey)
  url = baseUrl + ("/api/%s=%s/tags" % (param, value))
  header = {"Authorization": "bearer " + OauthToken}
  response = requests.get(url, headers = header).json()
  return response

def getUUID(sensor,cid, ckey):
  try:
    sensorUUID = list_sensor(cid, ckey)["data"][sensor]["name"]
  except Exception as e:
    return ""

  return sensorUUID

def read_tags(sensor, cid, ckey):
  sensorUUID = getUUID(sensor,cid, ckey)
  OauthToken = getOauthToken(cid, ckey)
  url = baseUrl + ("/api/sensor/%s/tags" % (sensorUUID))
  header = {"Authorization": "bearer " + OauthToken}  
  response = requests.get(url, headers = header).json()
  return response

def get_users(usergroup, cid, ckey):
  OauthToken = getOauthToken(cid, ckey)
  url = baseUrl+("/api/usergroup/%s/users" % (usergroup))
  header = {"Authorization": "bearer " + OauthToken} 
  response = requests.get(url, headers = header).json()
  return response

def create_sensorgroup(name, building, description):
  url = baseUrl+("/api/sensorgroup_create/name=%s/building=%s/description=%s" % (name, building, description))
  response = requests.post(url).json()
  return response

def post_timeseries_data(sensorUUID, email, payload, cid, ckey):
  OauthToken = getOauthToken(cid, ckey)
  header = {"Authorization": "bearer " + OauthToken, 'content-type':'application/json'}
  url = baseUrl + ("/api/data/id=%s/email=%s/actuation" % (sensorUUID, email))
  payload = json.dumps(payload)
  
  try:
    response = requests.post(url, headers = header, data = payload).json()
  except Exception as e:
    print "Invalid json in post"
    return {}

  return response

def get_timeseries_data(sensor, email, interval, cid, ckey):
  sensorUUID = getUUID(sensor, cid, ckey)

  if sensorUUID == "":
    return {}

  OauthToken = getOauthToken(cid, ckey)
  header = {"Authorization": "bearer " + OauthToken, 'content-type':'application/json'}
  email = email  
  url = baseUrl + "/api/data/id=%s/email=%s/interval=%s" % (sensorUUID, email, interval)
  
  try:
    response = requests.get(url, headers = header).json()
  except Exception as e:
    print "Invalid json in get"
    return {}
 
  return response

def dt(u): return datetime.datetime.fromtimestamp(u)

def writeFile(path, contents):
    with open(path, "a") as f:
        f.write(contents)

def getContents(response):
  if response["success"] != None and response["success"] == "False":
     return response["Error"]
  elif response["data"] == "None":
     return response["data"]
 
  result = ""
  values = response["data"]["series"][0]["values"]
  name = response["data"]["series"][0]["name"]
  
  for value in values:
    timestamp = str(dt(round(value[1])))
    val = str(value[2])
    result += timestamp + " : " + val + "\n"
  return name + result

def run_writer(sensor, email, cid, ckey):
  for x in range(0, 10):
    payload = {"data":[ { "value": random.randint(0,100),
                          "time": time.time() } ],
               "value_type":"Temperature" }
    writeFile("test_result.txt", "[" + email + "]" + " Transaction start\n")
    post_response = post_timeseries_data(sensor, email, payload, cid, ckey)
    pprint(post_response)
    writeFile("test_result.txt", "[" + email + "]" + " Transaction end : "+ str(post_response)+"\n") 
    time.sleep(1)

def run_reader(sensor, email, cid, ckey):
  interval = "2s"
  for x in range(0, 10):
    get_response = get_timeseries_data(sensor, email, interval, cid, ckey)
    pprint(get_response)
    writeFile("test_result.txt","["+ email +"]" + " Try read : " + str(get_response)+ "\n")
    time.sleep(1)

def list_subscriber_changes(email, cid, ckey):
  OauthToken = getOauthToken(cid, ckey)
  header = {"Authorization": "bearer " + OauthToken, 'content-type':'application/json'}
  url = baseUrl + ("/api/list/email=%s/changes" % (email))
  
  try:
    response = requests.get(url, headers = header).json()
  except Exception as e:
    print "Invalid json in list_subscriber_changes :" + str(e)
    return {}
 
  return response 

baseUrl = "http://mesl-exp.ucsd.edu:82" 
email = "bd_connector@ucsd.edu"
cid = "414bC6yEnUYwKnBhIHRh83mZESwUNhfCrVDy3KV7"
ckey = "Hy8O8UAAus0LunXRFZGXbsnMJXte2EifkbKiWBRYsRKQ2yiAWG"

while True:
  time.sleep(5) # assume subscription interval 
  response = list_subscriber_changes(email, cid, ckey)
  print response
  sensors = response['data'].keys()
  
  time.sleep(0.5) #assume BACnet delay 0.5s  
  for sensorUUID in sensors:
    obj = eval(response['data'][sensorUUID])

    payload = {"data":[ { "value": obj[0]['fields']['value'] ,
                          "time": time.time() } ],
               "value_type":"Temperature" }
    post_response = post_timeseries_data(sensorUUID, email, payload, cid, ckey)
    pprint(post_response)
  sensors = []
