"""
CentralService.rest_api.tagtype
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the interactions with the tagtypes. Takes care
of all the CRUD operations on the tagtypes. Each tagtype can have
parent and children tagtypes specifed for it.

@copyright: (c) 2016 SynergyLabs
@license: See License file for details.
"""

from flask.views import MethodView
from flask import request, jsonify
from ...models.cs_models import TagType, BuildingTemplate
from ..helper import add_delete, gen_update, get_email, check_if_super, check_oauth
from .. import responses
from ... import oauth
from ...auth.access_control import super_required


class TagTypeService(MethodView):
    params = ['name', 'description', 'parents', 'acl_tag']

    @check_oauth
    def post(self):
        try:
            data = request.get_json()['data']
        except KeyError:
            return jsonify(responses.missing_data)
        parents = data.get('parents')
        name = data.get('name')
        acl_tag = data.get('acl_tag')
        tagtype = TagType.objects(name=data.get('name')).first()

        if not tagtype:
            if name is None:
                return jsonify(responses.missing_parameters)
            if parents:
                for parent in parents:
                    if TagType.objects(name=parent).first() is None:
                        return jsonify(responses.invalid_parent_tags)
            data['acl_tag'] = check_if_super(get_email())
            TagType(**gen_update(self.params, data)).save()
            if parents:
                self.add_children(parents, name)
        else:
            collection = TagType._get_collection()
            if parents:
                added, deleted = add_delete([str(child_tag) for child_tag in tagtype['parents']], data['parents'])
                self.add_children(added, name)
                for tag in deleted:
                    collection = TagType._get_collection()
                    collection.update({'name': tag},
                                      {'$pull': {'children': name}},
                                      multi=True)
            user_check = check_if_super(get_email())
            if (acl_tag is None) or (acl_tag is not None and not user_check):
                data['acl_tag'] = user_check
            collection.update({'name': name}, {'$set': gen_update(self.params, data)})
        return jsonify(responses.success_true)

    @check_oauth
    def get(self, name):
        tagtype = TagType.objects(name=name).first()
        if tagtype:
            return jsonify({'success': 'True', 'name': tagtype['name'],
                            'description': tagtype['description'],
                            'parents': tagtype['parents'],
                            'children': tagtype['children']})
        else:
            return jsonify(responses.invalid_tagtype)

    @check_oauth
    @super_required
    def delete(self, name):
        print "in the rest api call"
        tagtype = TagType.objects(name=name).first()
        if not tagtype:
            return jsonify(responses.invalid_tagtype)

        if not tagtype.children and BuildingTemplate._get_collection().find({'tag_types': tagtype.name}).count() == 0:
            tagtype.delete()
            collection = TagType._get_collection()
            collection.update({'children': name},
                              {'$pull': {'children': name}},
                              multi=True)
            return jsonify(responses.success_true)
        else:
            return jsonify(responses.tagtype_referenced)

    def add_children(self, parents, name):
        for parent in parents:
            collection = TagType._get_collection()
            collection.update(
                {'name': parent},
                {'$addToSet': {'children': str(name)}}
            )
