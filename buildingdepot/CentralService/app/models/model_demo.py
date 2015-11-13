from cs_models import *
from mongoengine import connect

connect('buildingdepot')
data = {
    'name': 'ECE',
    'template': 't1',
    'description': 'basic',
    'metadata': {'length': 1},
    'tags': [
        {
            'name': 'floor',
            'value': '456',
            'metadata': {},
            'parents': []
        },
        {
            'name': 'room',
            'value': '123',
            'metadata': {},
            'parents': [
                {
                    'name': 'floor',
                    'value': '456'
                }
            ]
        },
        {
            'name': 'room',
            'value': '124',
            'metadata': {},
            'parents': [
                {
                    'name': 'floor',
                    'value': '456'
                }
            ]
        }
    ]
}

# Building(name=data['name'],
#          template=data['template'],
#          description=data['description'],
#          metadata=data['metadata'],
#          tags=data['tags']).save()
# print Building._get_collection().find(
#     {   'name': 'ECE',
#         'tags': {
#             '$elemMatch': {
#                 'name': 'floor',
#                 'value': '456'
#             }
#         }
#     }
# )[0]

print Building._get_collection().aggregate([
    {'$unwind': '$tags'},
    {'$match': {'name': 'ECE', 'tags.name': 'floor', 'tags.value': '456'}},
    {'$project': {'_id': 0, 'tags.ancestors': 1}}
])['result'][0]['tags']['ancestors']