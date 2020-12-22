""" A simple script to process the instrumentation logs and extract useful 
	statistics from it. This script currently supports computing the average
	time taken for every function. 
"""

import csv
import sys

filename = sys.argv[1]
averages = {}  # Mapping between function and total time taken + elements seen

"""
LOG FORMAT (comma separated):
[depth number of '\t's] <UNIQUE_CALL_ID>,<call_stack_depth>,<func_name>,<begin_time>,<end_time>,<time_taken>

e.g. 185618305,0,sensor_timeseries,41092.3860073,41124.2940426,31.9080352783
        185618305,1,write_timeseries_data,41105.2598953,41124.270916,19.0110206604

"""

f = open(filename, "rb")
reader = csv.reader(f)
logs = list(reader)
for log in logs:
    if log[2] in list(averages.keys()):
        averages[log[2]][0] += float(log[5])
        averages[log[2]][1] += 1
    else:
        averages[log[2]] = [float(log[5]), 1]

print("\nAVERAGES FOR TIME TAKEN (Function wise): ")
for key, value in list(averages.items()):
    print(
        (
            "  "
            + key
            + "(): "
            + str(value[0] / value[1])
            + "ms ("
            + str(value[1])
            + " calls)"
        )
    )

print()
