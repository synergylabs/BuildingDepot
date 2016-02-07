"""
    The instrumentation framework for BuildingDepot. Whenever it is enabled,
    the framework captures different calls made to the system when the 
    '@instrument' decorator is used. It assigns a unique number for every
    request and gives logical sequence IDs for cascaded calls. It measures the 
    time taken for each call and writes to the logs. To improve performance,
    the sampling rate can be reduced and this uniformly randomly drops some 
    logs.

    LOG FORMAT (comma separated vector):
    [depth number of '\t's] <UNIQUE_CALL_ID>,<call_stack_depth>,<func_name>,<begin_time>,<end_time>,<time_taken>

    e.g. 185618305,0,sensor_timeseries,41092.3860073,41124.2940426,31.9080352783
            185618305,1,write_timeseries_data,41105.2598953,41124.270916,19.0110206604 
"""

import thread
import time
from functools import wraps
import traceback
import os
import random

global process_unique_id
global seq_dict

seq_dict = {}
process_unique_id = 0
logs = []
beginningOfTime = time.time()

# Location of file where the instrumentation logs will be written to
logfile = '/srv/buildingdepot/Instrumentation/instrument.csv'

# Toggle for enabling/disabling instrumentation
enable_instrumentation = True

# Set the sampling rate here (0 to 1 - float). e.g. sampling rate 0.7 means
# that only 70% of the logs are collected (uniformly randomly) and rest are dropped.
sampling_rate = 1


"""A unique ID needs to be generated for every request so that all the 
   calls made by it can be tracked sequentially. The unique ID is generated 
   using a Cantor pairing function. 
"""
def compute_request_id():
    global process_unique_id
    pid = os.getpid()
    # Using Cantor pairing function
    val = process_unique_id + pid
    request_id = process_unique_id + (((val)*(val + 1))/2)
    return str(request_id)


def instrument(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        global seq_dict
        global process_unique_id
        global enable_instrumentation
        global logs

        if enable_instrumentation is False:
            return func(*args, **kwargs)

        if random.random() > sampling_rate:
            return func(*args, **kwargs)

        # Compute the unique request ID
        request_id = compute_request_id()
        seq = seq_dict[request_id]

        # Update sequence ID
        seq_dict[request_id] = seq + 1

        # Time the function execution
        start = (time.time() - beginningOfTime)*1000
        ret = func(*args, **kwargs)
        end = (time.time() - beginningOfTime)*1000
        
        # Format the log string
        logString = request_id + "," + str(seq) + "," + func.__name__ + ","

        for i in range(0,seq):
            logString = "\t" + logString

        logString = logString + "%0.2f,%0.2f,%0.2f\n" % (start, end, end-start)
        logs.append(logString)

        # Flush logs to file
        if seq == 0:
            logs = sorted(logs, key=lambda str: str.strip())
            with open(logfile, 'a') as file:
                for item in logs:
                    file.write(item)
            del logs[:]
        return ret
    return func_wrapper
