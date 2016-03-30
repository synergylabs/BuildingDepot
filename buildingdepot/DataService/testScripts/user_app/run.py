import sys, os, thread, requests, json, time, random, threading, datetime, signal, sys
from users import info
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
    response = requests.get(url, headers = header)
    if response.status_code != 401:
      return response.json()
    else:
      return {}
  except Exception as e:
    print " Invalid json in list_sensor : " + str(e) 
    return {}

def getUUID(sensor, cid, ckey):
  try:
    sensorUUID = list_sensor(cid, ckey)
    if sensorUUID == {}:
      return ""
    else:
      return sensorUUID["data"][sensor]["name"]
  except Exception as e:
    return ""

def post_timeseries_data(sensor, email, payload, cid, ckey):
  sensorUUID = getUUID(sensor, cid, ckey)
  
  if sensorUUID == "":
    print "UUID is wrong"
    return {}

  OauthToken = getOauthToken(cid, ckey)
  header = {"Authorization": "bearer " + OauthToken, 'content-type':'application/json'}
  url = baseUrl + ("/api/data/id=%s/email=%s/actuation" % (sensorUUID, email))
  payload = json.dumps(payload)
  try:
    response = requests.post(url, headers = header, data = payload)

    if response.status_code == 200:
      return response.json()
    else:
      print "Error : " + str(response.status_code)
      return {}
  except Exception as e:
    print "Invalid json in post : " + str(e)
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

def run_writer(sensor, email, cid, ckey, freq):
  global elapsed_time_write, num_writes, num_violation, num_timeout, num_server_errors, elapsed_time_timeout, elapsed_time_violation, num_unknown, num_corruption

  for x in range(0, freq):
    value = random.randint(0,100)
    payload = {"data":[ { "value": value,
                          "time": time.time() } ],
               "value_type":"Temperature" }
    #print (" [" + email + "]" + " Transaction start\n")
    print "Send : " + str(payload)
 
    start = datetime.datetime.now()
    post_response = post_timeseries_data(sensor, email, payload, cid, ckey)
    end = datetime.datetime.now()
    
    if post_response != {}:
      print("Receive : " + str(post_response))
      if "Error" in post_response.keys():
        if "lock" in post_response['Error'] :
          num_violation += 1
          elapsed_time_violation += (end - start)
        elif "timeout" in post_response['Error']:
          num_timeout += 1 
          elapsed_time_timeout += (end - start)
        else:
          num_unknown += 1
      else:
        returned_value = post_response['data']['series'][0]['values'][0][2]
        if returned_value != value :
          num_corruption += 1       
       
        num_writes += 1
        elapsed_time_write += (end - start)
    else:
      num_server_errors += 1
    time.sleep(1)  

def run_reader(sensor, email, cid, ckey, freq):
  global elapsed_time_read
  global num_reads
  global num_server_errors

  interval = "60s"
  for x in range(0, freq):
    start = datetime.datetime.now()
    get_response = get_timeseries_data(sensor, email, interval, cid, ckey)
    end = datetime.datetime.now()
    
    if get_response == {}:
      num_server_errors += 1
    else:  
      elapsed_time_read += (end - start)
      num_reads += 1
    pprint(get_response)
    
elapsed_time_read = (datetime.datetime.now() - datetime.datetime.now())
elapsed_time_write = (datetime.datetime.now() - datetime.datetime.now())
elapsed_time_timeout = (datetime.datetime.now() - datetime.datetime.now())
elapsed_time_violation = (datetime.datetime.now() - datetime.datetime.now())
num_server_errors = 0
num_timeout = 0
num_violation = 0
num_writes = 0
num_reads = 0
num_unknown = 0
num_corruption = 0
baseUrl = "http://mesl-exp.ucsd.edu:82"  
try_multi_sensors = False
argu = sys.argv


if len(argu) <= 6:
  print "Too few argumets. example: python run.py -{dw/ew} -{dr/er} 2{number of writers} 10{number of write requests per writer} 1{number of reader} 2{number of read requests per reader}"
  exit(1)
if 'dw' in argu[1] :
  try_multi_actuators = True
elif 'ew' in argu[1] :
  try_multi_actuators = False

if 'dr' in argu[2] :
  try_multi_readers = True
elif 'er' in argu[2] :
  try_multi_readers = False

num_writer = int(argu[3])
freq_writer = int(argu[4])
num_reader = int(argu[5])
freq_reader = int(argu[6])

print "Number of writers : " + str(num_writer)
print "Frequency of writing : " + str(freq_writer)
print "Number of readers : " + str(num_reader)
print "Frequency of reading : " + str(freq_reader)

sensors = ["sensor_"+ str(x) for x in range (1,100)] # sensor_X, X means the place or sensors in Sensor table (Honam: somewhat weird. it should be fixed)
sensor = sensors[0] # 1st sensor is 3afadf60-742d-45ad-8dfa-28b18bb7f60b for now.

for x in range(0, num_writer):
  if try_multi_actuators :
    sensor = sensors[x]
  print sensor
  email = info[x]["email"]
  cid = info[x]["cid"]
  ckey = info[x]["ckey"] 
  thread.start_new_thread(run_writer, (sensor, email, cid, ckey, freq_writer,))
  time.sleep(1)

sensor = sensors[0]  
for y in range(num_reader, 0, -1): #To avoid ID duplications, iterate in reverse order.
  if try_multi_readers :
    sensor = sensors[y]
  email = info[y]["email"]
  cid = info[y]["cid"]
  ckey = info[y]["ckey"] 
  thread.start_new_thread(run_reader, (sensor, email, cid, ckey, freq_reader,))
  
print "Waiting for children...."
time.sleep(10)

while True:
  time.sleep(5)
  print "Number of successful writes : " + str(num_writes)
  print "Number of successful reads : " + str(num_reads)
  print "Number of emulator errors : " + str(num_server_errors)
  print "Number of internal server errors : " + str(num_unknown)
  print "Number of failure of acquiring a lock error : " + str(num_violation)
  print "Number of transaction timeout error : " + str(num_timeout) 
  print "Number of data corruptions : " + str(num_corruption)

  if num_writes != 0:
    print "average latency of successful write : " + str((elapsed_time_write.total_seconds()*1000)/num_writes)
  if num_timeout != 0:
    print "average latency of timeout write : " + str((elapsed_time_timeout.total_seconds()*1000)/num_timeout)
  if num_violation:
    print "average latency of violation write : " + str((elapsed_time_violation.total_seconds()*1000)/num_violation)
  print "---------------------------------------"
  if num_reads != 0:
    print "average latency of successful read : " + str((elapsed_time_read.total_seconds()*1000)/num_reads)

  if (num_writes + num_server_errors + num_violation + num_timeout + num_reads) == (num_writer * freq_writer + num_reader * freq_reader):
    break


