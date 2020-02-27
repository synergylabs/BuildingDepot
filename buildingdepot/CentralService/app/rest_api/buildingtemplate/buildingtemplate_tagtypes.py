"""
CentralService.rest_api.buildingtemplate_tagtypes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the interactions with the buildingtemplate tagtypes. Takes care
of all the CRUD operations on buildingtemplate tagtypes.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask.views import MethodView
from flask import request, jsonify

from ...models.cs_models import BuildingTemplate, TagType
from .. import responses
from ..helper import check_oauth


class BuildingTemplateTagtypeService(MethodView):
    @check_oauth
    def post(self, name):
        building_template = BuildingTemplate.objects(name=name).first()
        if building_template is None:
            return jsonify(responses.invalid_template)
        data = request.get_json()["data"]

        def tagtype_exists(tagtype):
            return TagType.objects(name=tagtype).first()

        valid_tagtypes = []
        invalid_tagtypes = []
        for tagtype in data["tagtypes"]:
            if tagtype_exists(tagtype):
                valid_tagtypes.append(tagtype)
            else:
                invalid_tagtypes.append(tagtype)

        return (
            jsonify({"success": "True", "invalid_tagtypes": invalid_tagtypes})
            if building_template.update(add_to_set__tag_types=valid_tagtypes)
            else jsonify({"success": "False"})
        )

    @check_oauth
    def get(self, name):
        buildingtemplate = BuildingTemplate.objects(name=name).first()
        if buildingtemplate is None:
            return jsonify(responses.invalid_template)
        response = dict(responses.success_true)
        response.update({"tag_types": buildingtemplate.tag_types})
        return jsonify(response)

    @check_oauth
    def delete(self, name):
        buildingtemplate = BuildingTemplate.objects(name=name).first()
        if buildingtemplate is None:
            return jsonify(responses.invalid_template)
        data = request.get_json()["data"]
        return (
            jsonify(
                {
                    "success": "True",
                    "tagtypes_absent": list(
                        set(data["tagtypes"]) - set(buildingtemplate.tag_types)
                    ),
                }
            )
            if buildingtemplate.update(pull_all__tag_types=data["tagtypes"])
            else jsonify({"success": "False"})
        )

    @check_oauth
    def put(self, name):
        buildingtemplate = BuildingTemplate.objects(name=name).first()
        if buildingtemplate is None:
            return jsonify(responses.invalid_template)
        data = request.get_json()["data"]
        tagtype_exists = lambda tagtype: TagType.objects(name=tagtype).first()
        valid_tagtypes = filter(tagtype_exists, data["tagtypes"])
        return (
            jsonify(
                {
                    "success": "True",
                    "invalid_tagtypes": list(
                        set(data["tagtypes"]) - set(valid_tagtypes)
                    ),
                }
            )
            if buildingtemplate.update(set__tag_types=valid_tagtypes)
            else jsonify({"success": "False"})
        )
