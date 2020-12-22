"""
CentralService.rest_api.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains all the definitions for the REST api's that are exposed to the user.
All requests will need to be authenticated using an OAuth token and sensor specific
requests will also have an additional check where the ACL's are referenced to see if
the user has access to the specific sensor

@copyright: (c) 2020 SynergyLabs
@license: CMU License. See License file for details.
"""
from flask import request, jsonify

from . import api
from ..models.cs_models import *


@api.route("/buildingtemplate/<name>/edit", methods=["POST"])
def buildingtemplate_tag_edit(name):
    data = list(map(str, request.get_json()["data"]))
    buildingtemplate = BuildingTemplate.objects(name=name).first()
    if buildingtemplate.update(set__tag_types=data):
        return jsonify({"success": "True"})
    else:
        return jsonify({"success": "False"})


@api.route("/tagtype/list", methods=["GET"])
def api():
    # collection = TagType._get_collection().find()
    all_tags = []
    collection = TagType.objects
    for i in collection:
        all_tags.append(i.name)
    return jsonify({"success": "True", "tags": all_tags})
