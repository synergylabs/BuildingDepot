#!/usr/bin/env python
import pika, sys, os, thread, requests, json, time, random, threading, datetime
from pprint import pprint

def getOauthToken(cid, ckey):
  url = baseUrl+"/oauth/access_token/client_id="+cid+"/client_secret="+ckey
  response = requests.get(url).json()
  access_token = response["access_token"]
  return access_token

def post_timeseries_data(sensorUUID, email, payload, cid, ckey):
  OauthToken = getOauthToken(cid, ckey)
  header = {"Authorization": "bearer " + OauthToken, 'content-type':'application/json'}
  url = baseUrl + ("/api/data/id=%s/email=%s/timeseries" % (sensorUUID, email))
  payload = json.dumps(payload)

  try:
    response = requests.post(url, headers = header, data = payload).json()
  except Exception as e:
    print "Invalid json in post: " + str(e)

    return {}

  return response

def callback(ch, method, properties, body): 
    # 1. Received a push msg from BD queue  and transform to json()
    # 2. Send the actuatation request to BACnet"
    # 3. Get response from BACnet
    # 4. Update the result to BD by calling the API sensor_timeseries()
    
    global cid, ckey
    sensorUUID = method.routing_key
    print(" [x] %r:%r" % (method.routing_key, body)) 
    body = eval(body)
    
    # Assume it sends actuation request to BACnet
    # Assume it receives a response from BACnet
    
    # Update the result to BD
    payload = {"data":[ { "value": body[0]['fields']['value'] , "time": body[0]['fields']['timestamp']} ]}
    post_response = post_timeseries_data(sensorUUID, email, payload, cid, ckey)
    pprint(post_response)

baseUrl = "http://mesl-exp.ucsd.edu:82" 
email = "bd_connector@ucsd.edu"
cid = "414bC6yEnUYwKnBhIHRh83mZESwUNhfCrVDy3KV7"
ckey = "Hy8O8UAAus0LunXRFZGXbsnMJXte2EifkbKiWBRYsRKQ2yiAWG"

sensorUUID = "3afadf60-742d-45ad-8dfa-28b18bb7f60b" # target sensor UUID
app_id = "amq.gen-rsZbjlkUZkQZpj0qsPbPNA" # app's queue id

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.exchange_declare(exchange='master_exchange', type='direct')

print(' [*] Waiting for logs. To exit press CTRL+C')

channel.basic_consume(callback, queue=app_id, no_ack=True)
channel.start_consuming()
