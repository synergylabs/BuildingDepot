
from os import listdir
import json
for f in listdir('.'):
	if f == 'parse.py':
		continue
	with open('./'+f) as d:
		try:
			data = json.load(d)
			print(data['title'] , data['requests']['total'] , data['requests']['average'] , data['latency']['p99'] , data['throughput']['total'] , data['throughput']['average'] , data['connections'] , data['duration'] , data['non2xx'], sep='\t')   
		except Exception as e:
			pass