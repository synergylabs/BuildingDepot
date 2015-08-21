from mongoengine import connect
from app.api_0_0.resources.write import *

connect('dataservice')
#	host='127.0.0.1',
#	port=27017)

testWrite = Write()
testWrite.get(sensor_name="44246a86-109e-4fd5-bb23-c1b3fd605c2f")

