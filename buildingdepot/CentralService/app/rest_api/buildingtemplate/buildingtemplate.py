"""
CentralService.rest_api.buildingtemplate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the interactions with the building templates. Takes
care of all the CRUD operations on the buildingtemplates.
Each buildingtemplate will have a list of tagtypes attached to it that
can be used by all buildings that are based on that specific building
template.

@copyright: (c) 2024 SynergyLabs
@license: CMU License. See License file for details.
"""
from flask import jsonify, request
from flask.views import MethodView

from .. import responses
from ..helper import add_delete, gen_update, check_oauth
from ... import oauth
from ...auth.access_control import super_required
from ...models.cs_models import TagType, BuildingTemplate, Building


class BuildingTemplateService(MethodView):
    params = ["name", "description", "tag_types"]

    @check_oauth
    @super_required
    def post(self):
        try:
            data = request.get_json()["data"]
        except KeyError:
            return jsonify(responses.missing_data)
        try:
            name = data["name"]
        except:
            return jsonify(responses.missing_parameters)
        if not name:
            return jsonify(
                {"success": "False", "error": "Invalid Building Template name."}
            )
        template = BuildingTemplate.objects(name=name).first()
        tagtypes = data.get("tag_types")
        if not tagtypes:
            tagtypes = []
        for tagtype in tagtypes:
            if TagType.objects(name=tagtype).first() is None:
                return jsonify(responses.invalid_tagtypes)

        if template is None:
            BuildingTemplate(**gen_update(self.params, data)).save()
        else:
            added, deleted = add_delete(template["tag_types"], tagtypes)
            collection = Building._get_collection()
            for tagtype in deleted:
                if collection.count_documents({"template": name, "tags.name": name}) > 0:
                    return jsonify(responses.tagtype_in_use)
            collection = BuildingTemplate._get_collection()
            collection.update_one({"name": name}, {"$set": gen_update(self.params, data)})
        return jsonify(responses.success_true)

    @check_oauth
    def get(self, name):
        template = BuildingTemplate.objects(name=name).first()
        if template is None:
            return jsonify(responses.invalid_template)
        response = dict(responses.success_true)
        response.update(
            {
                "name": template["name"],
                "description": template["description"],
                "tag_types": template["tag_types"],
            }
        )
        return jsonify(response)

    @check_oauth
    @super_required
    def delete(self, name):
        template = BuildingTemplate.objects(name=name).first()
        if template is None:
            return jsonify(responses.invalid_template)

        if Building.objects(template=name).count() > 0:
            return jsonify(responses.template_in_use)

        template.delete()
        return jsonify(responses.success_true)
