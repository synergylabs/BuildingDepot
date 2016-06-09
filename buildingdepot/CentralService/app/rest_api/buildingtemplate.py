"""
CentralService.rest_api.buildingtemplate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the interactions with the building templates. Takes
care of all the CRUD operations on the buildingtemplates.
Each buildingtemplate will have a list of tagtypes attached to it that
can be used by all buildings that are based on that specific building
template.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""
from flask import jsonify,request
from flask.views import MethodView
from . import responses
from .helper import add_delete,gen_update
from ..models.cs_models import TagType,BuildingTemplate,Building

class BuildingTemplateService(MethodView):

    params = ['name','description','tag_types']

    def post(self):
        try:
            data = request.get_json()['data']
        except KeyError:
            return jsonify(responses.missing_data)
        try:
            name = data['name']
        except:
            return jsonify(responses.missing_parameters)

        template = BuildingTemplate.objects(name=name).first()
        tagtypes = data.get('tag_types')
        for tagtype in tagtypes:
            if TagType.objects(name=tagtype).first() is None:
                return jsonify(responses.invalid_tagtypes)

        if template is None:
            BuildingTemplate(**gen_update(self.params,data)).save()
        else:
            added, deleted = add_delete(template['tag_types'],tagtypes)
            collection = Building._get_collection()
            for tagtype in deleted:
                if collection.find({"template":name,"tags.name":name}).count() > 0:
                    return jsonify(responses.tagtype_in_use)
            collection = BuildingTemplate._get_collection()
            collection.update({'name': name},{'$set':gen_update(self.params,data)})
        return jsonify(responses.success_true)

    def get(self,name):
        template = BuildingTemplate.objects(name=name).first()
        if template is None:
            return jsonify(responses.invalid_template)
        response = dict(responses.success_true)
        response.update({'name':template['name'],
                                    'description':template['description'],
                                    'tag_types':template['tag_types']})
        return jsonify(response)

    def delete(self,name):
        template = BuildingTemplate.objects(name=name).first()
        if template is None:
            return jsonify(responses.invalid_template)

        if Building.objects(template=name).count() > 0:
            return jsonify(responses.template_in_use)

        template.delete()
        return jsonify(responses.success_true)




