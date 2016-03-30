import sys, os, thread, requests, json, time, random, threading, datetime
from pprint import pprint

def getOauthToken(cid, ckey):
  url = baseUrl+"/oauth/access_token/client_id="+cid+"/client_secret="+ckey
  response = requests.get(url).json()
  access_token = response["access_token"]
  return access_token

def list_sensor():
  global cid, ckey, baseUrl

  OauthToken = getOauthToken(cid, ckey)
  url = baseUrl+"/api/list"
  header = {"Authorization": "bearer " + OauthToken}
 
  try:
    response = requests.get(url, headers = header).json()
  except Exception as e:
    print "Invalid json in list_sensor"
    return {}

  return response

def getUUID(sensor,cid, ckey):
  try:
    sensorUUID = list_sensor(cid, ckey)["data"][sensor]["name"]
  except Exception as e:
    return ""

  return sensorUUID

def register_subscription(sensorUUID):
  global cid, ckey, baseUrl, email, app_id

  OauthToken = getOauthToken(cid, ckey)
  header = {"Authorization": "bearer " + OauthToken, 'content-type':'application/json'}
  #header = {'content-type' : 'application/json'}
  url = baseUrl + "/api/apps/subscription"
  payload = json.dumps({ "email": email, "app": app_id, "sensor": sensorUUID})
  
  try:
    response = requests.post(url, headers = header, data = payload).json()
  except Exception as e:
    print "Invalid json : " + str(e)
    return {}
  
  return response

baseUrl = "http://mesl-exp.ucsd.edu:82"
email = "bd_connector@ucsd.edu"
cid = "414bC6yEnUYwKnBhIHRh83mZESwUNhfCrVDy3KV7"
ckey = "Hy8O8UAAus0LunXRFZGXbsnMJXte2EifkbKiWBRYsRKQ2yiAWG"
app_id = "amq.gen-rsZbjlkUZkQZpj0qsPbPNA" # app's queue id

list_sensor = list_sensor()["data"]
for sensor in list_sensor:
  response = register_subscription(list_sensor[sensor]["name"]) # Register Existing all sensors to a queue for test
  pprint(response)



