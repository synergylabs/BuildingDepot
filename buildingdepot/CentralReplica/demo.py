from models import *
connect('buildingdepot')

print Role.objects(name='default').first().permission

