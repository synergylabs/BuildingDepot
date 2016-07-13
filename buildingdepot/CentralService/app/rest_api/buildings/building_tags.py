"""
CentralService.rest_api.building_tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the interactions with the building tags. Takes care
of all the CRUD operations on building tags.
For each of the tagtypes present in the template on which this building is
based on, can have multiple unique values defined for them.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask.views import MethodView
from flask import request, jsonify
from ...models.cs_models import Building, BuildingTemplate
from ...models.cs_models import TagType, DataService, User
from .. import responses
from ..helper import get_email
from ... import oauth
from ...auth.access_control import super_required


class BuildingTagsService(MethodView):
    @oauth.require_oauth()
    def post(self, building_name):
        try:
            data = request.get_json()['data']
        except:
            return jsonify(responses.missing_data)
        try:
            name = data['name']
            value = data['value']
        except:
            return jsonify(responses.missing_parameters)
        collection = Building._get_collection()
        # Form the tag to update in MongoDB
        building = Building.objects(name=building_name).first()
        if building is None:
            return jsonify(responses.invalid_building)
        template = BuildingTemplate.objects(name=building['template']).first()
        if name not in template['tag_types']:
            return jsonify(responses.invalid_tagtype)
        collection = Building._get_collection()
        metadata = data.get('metadata')
        parents = data.get('parents')
        if parents and len(parents)!=0:
            search_list = []
            for element in parents:
                search_list.append({'$elemMatch': element})
            if collection.find({"tags": {"$all": search_list}}).count() == 0:
                return jsonify(responses.invalid_parents)
        tag = {
            'name': name,
            'value': value,
            'metadata': metadata if metadata else [],
            'parents': parents if parents else [],
        }
        tag_exists = collection.find({'tags':
                                          {"$elemMatch": {"name": name, "value": value}}})
        if tag_exists.count() == 0:
            collection.update(
                {'name': building_name},
                {'$addToSet': {'tags': tag}}
            )
        else:
            if parents:
                collection.update({'name': building_name,
                                   'tags': {"$elemMatch": {"name": name, "value": value}}},
                                  {"$set": {"tags.$.parents": []}})
                collection.update({'name': building_name,
                                   'tags': {"$elemMatch": {"name": name, "value": value}}},
                                  {"$push": {"tags.$.parents": {"$each": parents}}})
        return jsonify(responses.success_true)

    @oauth.require_oauth()
    def get(self, building_name):
        building = Building.objects(name=building_name).first()
        if building is None:
            return jsonify(responses.invalid_building)
        template = building['template']
        names = BuildingTemplate.objects(name=template).first().tag_types
        pairs = {name: TagType.objects(name=name).first().parents for name in names}
        tags = Building._get_collection().find(
            {'name': building_name},
            {'_id': 0, 'tags.name': 1, 'tags.value': 1, 'tags.parents': 1}
        )[0]['tags']
        parents = set([pair['name'] + pair['value'] for tag in tags for pair in tag['parents']])
        # Response contains parameters that define whether tag can be deleted or not
        for tag in tags:
            tag['can_delete'] = tag['name'] + tag['value'] not in parents
        response = dict(responses.success_true)
        response.update({'pairs': pairs, 'tags': tags})
        return jsonify(response)

    @oauth.require_oauth()
    def delete(self, building_name):
        building = Building.objects(name=building_name).first()
        if building is None:
            return jsonify(responses.invalid_building)
        try:
            data = request.get_json()['data']
        except:
            return jsonify(responses.missing_data)
        try:
            name = data['name']
            value = data['value']
        except:
            return jsonify(responses.missing_parameters)

        collection = Building._get_collection()
        tag_exists = collection.find({'tags':
                                          {"$elemMatch": {"name": name, "value": value}}})
        if tag_exists.count() == 0:
            return jsonify(responses.invalid_tag_value)
        tag_use = collection.find({'tags.parents':
                                       {"$elemMatch": {"name": name, "value": value}}})
        if tag_use.count() > 0:
            return jsonify(responses.tagtype_referenced)
        collection.update({'name': building_name},
                          {'$pull': {'tags': {'name': name, 'value': value}}})
        return jsonify(responses.success_true)
