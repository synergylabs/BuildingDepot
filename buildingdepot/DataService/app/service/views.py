"""
DataService.service.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains all the definitions for the frontend functions. Any action on the
Web interface will generate a call to one of these functions that renders
a html page.

For example opening up http://localhost:81/service/sensor on your installation
of BD will call the sensor() function

@copyright: (c) 2020 SynergyLabs
@license: CMU License. See License file for details.
"""

import math
import sys
from flask import json, render_template, request
from flask import session, redirect, url_for, jsonify, flash
from uuid import uuid4

from . import service
from .forms import *
from .. import r, influx, permissions
from ..models.ds_models import *
from ..rest_api import responses
from ..rest_api.helper import form_query, get_building_tags
from ..rest_api.utils import *

sys.path.append("/srv/buildingdepot")
from ..api_0_0.resources.utils import *
from ..api_0_0.resources.acl_cache import invalidate_permission


@service.route("/sensor", methods=["GET", "POST"])
def sensor():
    # Show the user PAGE_SIZE number of sensors on each page
    page = request.args.get("page", 1, type=int)
    skip_size = (page - 1) * PAGE_SIZE
    objs = (
        Sensor.objects(source_identifier__ne="SensorView")
        .skip(skip_size)
        .limit(PAGE_SIZE)
    )
    for obj in objs:
        obj.can_delete = True
    total = Sensor.objects(source_identifier__ne="SensorView").count()
    if total:
        pages = int(math.ceil(float(total) / PAGE_SIZE))
    else:
        pages = 0
    return render_template(
        "service/sensor.html",
        objs=objs,
        total=total,
        pages=pages,
        current_page=page,
        pagesize=PAGE_SIZE,
    )


@service.route("/sensor/search", methods=["GET", "POST"])
def sensors_search():
    data = json.loads(request.args.get("q"))
    print((data, type(data)))
    args = {}
    for key, values in list(data.items()):
        if key == "Building":
            form_query("building", values, args, "$or")
        elif key == "SourceName":
            form_query("source_name", values, args, "$or")
        elif key == "SourceIdentifier":
            form_query("source_identifier", values, args, "$or")
        elif key == "ID":
            form_query("name", values, args, "$or")
        elif key == "Tags":
            form_query("tags", values, args, "$and")
        elif key == "MetaData":
            form_query("metadata", values, args, "$and")
    print(args)
    # Show the user PAGE_SIZE number of sensors on each page
    page = request.args.get("page", 1, type=int)
    skip_size = (page - 1) * PAGE_SIZE
    collection = Sensor._get_collection().find(args)
    sensors = collection.skip(skip_size).limit(PAGE_SIZE)

    sensor_list = []
    for sensor in sensors:
        sensor = Sensor(**sensor)
        sensor.can_delete = True
        sensor_list.append(sensor)

    total = collection.count()
    if total:
        pages = int(math.ceil(float(total) / PAGE_SIZE))
    else:
        pages = 0
    return render_template(
        "service/sensor.html",
        objs=sensor_list,
        total=total,
        pages=pages,
        current_page=page,
        pagesize=PAGE_SIZE,
    )


@service.route("/sensor/<name>/tags")
def get_sensor_tags(name):
    obj = Sensor.objects(name=name).first()
    tags_owned = [{"name": tag.name, "value": tag.value} for tag in obj.tags]
    tags = get_building_tags(obj.building)
    response = dict(responses.success_true)
    response.update({"tags": tags, "tags_owned": tags_owned})
    return jsonify(response)


@service.route("/graph/<name>")
@service.route("/sensor/graph/<name>")
def graph(name):
    objs = Sensor.objects()
    for obj in objs:
        if obj.name == name:
            temp = obj
            break
    metadata = Sensor._get_collection().find({"name": name}, {"metadata": 1, "_id": 0})[
        0
    ]["metadata"]
    metadata = [{"name": key, "value": val} for key, val in list(metadata.items())]
    obj = Sensor.objects(name=name).first()
    tags_owned = [{"name": tag.name, "value": tag.value} for tag in obj.tags]
    return render_template(
        "service/graph.html", name=name, obj=temp, metadata=metadata, tags=tags_owned
    )
