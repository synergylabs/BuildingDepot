from app.models.cs_models import User, Building, TagType, BuildingTemplate, Role
from flask.ext.restful import marshal, fields
from mongoengine import connect
connect('buildingdepot')

# res = {
#     'role': fields.String,
#     'building': fields.String
# }
#
# paris = [
#     {
#         'role': 'default',
#         'building': 'ECE'
#     },
#     {
#         'role': 'default',
#         'building': 'CSE'
#     }
#
# ]
#
# collection = Building._get_collection()
#
# print Building._get_collection().aggregate([
#             {'$unwind': '$tags'},
#             {'$match': {'name': 'ECE', 'tags.name': 'floor', 'tags.value': '2'}},
#             {'$project': {'_id': 0, 'tags': 1}}
# ])['result'][0]['tags']
print Building._get_collection().find({'name': 'ECE'}, {'tags.name': 1, 'tags.value': 1, '_id': 0})[0]['tags']