from mongoengine import connect
connect('buildingdepot')
from cs_models import BuildingTemplate

a = BuildingTemplate.objects(name='t1').first()
print a.tag_types