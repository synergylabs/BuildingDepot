"""
DataService.service.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains all the definitions for the frontend functions. Any action on the
Web interface will generate a call to one of these functions that renders
a html page.

For example opening up http://localhost:81/service/sensor on your installation
of BD will call the sensor() function

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask import json, render_template, request
from flask import session, redirect, url_for, jsonify, flash
from . import service
from ..models.ds_models import *
from .forms import *
from ..rest_api.utils import *
from ..rest_api.helper import form_query,get_building_tags
from ..rest_api import responses
from uuid import uuid4
from .. import r, influx, permissions
import sys
import math

sys.path.append('/srv/buildingdepot')
from ..api_0_0.resources.utils import *
from ..api_0_0.resources.acl_cache import invalidate_permission


@service.route('/sensor', methods=['GET', 'POST'])
def sensor():
    # Show the user PAGE_SIZE number of sensors on each page
    page = request.args.get('page', 1, type=int)
    skip_size = (page - 1) * PAGE_SIZE
    objs = Sensor.objects().skip(skip_size).limit(PAGE_SIZE)
    for obj in objs:
        obj.can_delete = True
    total = len(Sensor.objects())
    if (total):
        pages = int(math.ceil(float(total) / PAGE_SIZE))
    else:
        pages = 0
    return render_template('service/sensor.html', objs=objs, total=total,
                           pages=pages, current_page=page, pagesize=PAGE_SIZE)


@service.route('/sensor/search', methods=['GET', 'POST'])
def sensors_search():
    data = json.loads(request.args.get('q'))
    print data, type(data)
    args = {}
    for key, values in data.iteritems(): # BIG CHANGES
              for key, values in data.iteritems():
	    Special = key[length(key)-1]
	    if Special in ['*', '+', '-']:
		newkey = key[:length(key)-1]
		if newkey = 'Type':
			form_query('Enttype', values, args, "$or")
			if Special == '*' or Special == '+':
				#Traverse Upwards
				loopvar = 1
				tempvalues = [values]
				newTemp = []
				while loopvar=1:
					loopvar = 0
					for singleValue in tempvalues:
						form_query("subClass", singleValue, tempargs,"$or")
						newCollect = BrickType._get_collection().find(tempargs)
						tempargs = []
						for newValue in newCollect:
							newName = newValue.get('name')
							form_query('Enttype', newName, args, "$or")
							newTemp.append(newName)
							loopvar = 1
						tempvalues = newTemp
						newTemp = []					
					
			if Special == '*' or Special =='-':
				#Traverse Downwards
				loopvar = 1
				tempvalues = [values]
				newTemp = []
				while loopvar=1:
					loopvar = 0
					for singleValue in tempvalues:
						form_query("superClass", singleValue, tempargs,"$or")
						newCollect = BrickType._get_collection().find(tempargs)
						tempargs = []
						for newValue in newCollect:
							newName = newValue.get('name')
							form_query('Enttype', newName, args, "$or")
							newTemp.append(newName)
							loopvar = 1
						tempvalues = newTemp
						newTemp = []			
			
		else:
		  	return jsonify(responses.no_search_parameters) 
            elif key == 'Type':
		form_query('Enttype', values, args, "$or")
	    elif key == 'Building':
                form_query('building',values,args,"$or")
            elif key == 'SourceName':
                form_query('source_name',values,args,"$or")
            elif key == 'SourceIdentifier':
                form_query('source_identifier',values,args,"$or")
            elif key == 'ID':
                form_query('name',values,args,"$or")
            elif key == 'Tags':
                form_query('tags',values,args,"$and")
            elif key == 'MetaData':
                form_query('metadata',values,args,"$and")    
    print args
    # Show the user PAGE_SIZE number of sensors on each page
    page = request.args.get('page', 1, type=int)
    skip_size = (page - 1) * PAGE_SIZE
    collection = Sensor._get_collection().find(args)
    sensors = collection.skip(skip_size).limit(PAGE_SIZE)

    sensor_list = []
    for sensor in sensors:
        sensor = Sensor(**sensor)
        sensor.can_delete = True
        sensor_list.append(sensor)

    total = collection.count()
    if (total):
        pages = int(math.ceil(float(total) / PAGE_SIZE))
    else:
        pages = 0
    return render_template('service/sensor.html', objs=sensor_list, total=total,
                           pages=pages, current_page=page, pagesize=PAGE_SIZE)

@service.route('/sensor/<name>/tags')
def get_sensor_tags(name):
    obj = Sensor.objects(name=name).first()
    tags_owned = [{'name': tag.name, 'value': tag.value} for tag in obj.tags] 
    tags = get_building_tags(obj.building) #Needs Change
    response = dict(responses.success_true)
    response.update({'tags': tags, 'tags_owned': tags_owned})
    return jsonify(response)

@service.route('/graph/<name>')
@service.route('/sensor/graph/<name>')
def graph(name):
    objs = Sensor.objects()
    for obj in objs:
        if obj.name == name:
            temp = obj
            break
    metadata = Sensor._get_collection().find({'name': name}, {'metadata': 1, '_id': 0})[0]['metadata']
    metadata = [{'name': key, 'value': val} for key, val in metadata.iteritems()]
    obj = Sensor.objects(name=name).first()
    tags_owned = [{'name': tag.name, 'value': tag.value} for tag in obj.tags]
    return render_template('service/graph.html', name=name, obj=temp, metadata=metadata, tags=tags_owned)

