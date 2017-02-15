"""
DataService.rest_api.sensor_tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the interactions with the sensor tags. Supports all
the CRUD operations on the tags of the sensor specified by the uuid. User
will have to have r/w/p permission to the sensor in order to be able to
update/remove tags from a sensor


@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""
import sys, json
from flask.views import MethodView
from flask import request,jsonify
from ..import responses
from ...models.cs_models import Sensor,SensorGroup
from ..helper import get_building_tags, form_query,create_response
from ... import r,oauth
from ...rpc import defs
from ...auth.access_control import authenticate_acl
import search
class SensorTagsService(MethodView):

    @oauth.require_oauth()
    def get(self,name):
        """
        Args as data:
        "name" : <sensor-uuid>

        Returns (JSON):
        {
          "tags": {
                   "Tag Name": [ List of eligible values],
                   .
                   .
                   .
                  }, (These are the list of eligibile tags for this sensor)
          "tags_owned": [
                          {
                           "name": <Tag-Name>,
                           "value": <Tag-Value>
                          },
                          .
                          .
                          .
                        ] (These are the list of tags owned by this sensor)
        } """
        obj = Sensor.objects(name=name).first()
        if obj is None:
	    print "I happen"
            return jsonify(responses.invalid_uuid)
	tags_owned = [{'name': tag.name, 'value': tag.value} for tag in obj.tags]
        print len(tags_owned), "length"
	print tags_owned
	tags = get_building_tags(obj.building) #NEEDS TO BE CHANGED
        response = dict(responses.success_true)
        response.update({'tags': tags, 'tags_owned': tags_owned}) #NEEDS TO BE CHANGED
        return jsonify(response)

    @oauth.require_oauth()
    @authenticate_acl('r/w/p')
    def post(self,name):
        """
        Args as data:
        "name" : <sensor-uuid>

        Following data in JSON:
        {
          "data": [
                   {
                    "name": <Tag-Name>,
                    "value": <Tag-Value>
                    },
                    .
                    .
                    .
                  ]
        }

        Returns:
        {
            "success": <True or False>
        }
     """
#	payload = {'data':[{
   #             'name': tagname,
  #              'value': tagvalue
 #           },{
#		'name':tagname2,
#		'value':tagvalue2}]}
#	SearchService.post(payload.json())
#	SensorTagService.post('newname')
        Recursedict = dict()
        Recursedict[name] = list()
        NewTags = request.get_json()['data']
        print NewTags, "CHECK IT"
        for tag in NewTags:
	 Recursedict[name].append(tag)
	 print tag, "here"
     
        while(len(Recursedict.keys())>0):
	 name = Recursedict.keys()[0]
	 print name, "NAME IS HERE"
         sensor = Sensor.objects(name=name).first()
	 #Brick Code Added Below
	 NewTags = Recursedict[name]
	 BrickTags = ['isLocatedIn', 'hasPoint', 'hasAbbreviation', 'hasSynonym', 'hasUnit', 'contains', 'feeds', 'hasProperty', 'actuates', 'controls', 'isInputOf', 'isOutputOf']
	 TagsAdded = list()
	 toBeIncluded = list()
	 tobeSearched = dict()
	 for tag in sensor.tags:
		TagsAdded.append(tag)
	 for tag in BrickTags:
		for addTags in NewTags:
			if(addTags['name'] == tag):
				toBeIncluded.append(addTags)
				if(addTags['name'] not in tobeSearched):
					tobeSearched[addTags['name']] = list()
				tobeSearched[addTags['name']].append(addTags['value'])
	#At this point, toBeIncluded has every BrickTag that the current sensor is being updated for. These Tags must go through the recursive update process. 
#	print name
        #NewTags = request.get_json()['data']
 #       print NewTags,type(NewTags)
 	# sensor = Sensor.objects(name=name).first()
 	 tags_owned = [{'name': tag.name, 'value': tag.value} for tag in sensor.tags]
	# tags_owned = []
	 for tag in NewTags:
		print tag['name'], tag['value'], "tags"
		if tag not in tags_owned:
			tags_owned.append(tag)
		else:
			print tag, "HERE WE GO"
         if defs.invalidate_sensor(name):
            if sensor is None:
                return jsonify(responses.invalid_uuid)
#	    NewList = []
#	    for key in tags.keys():
#		NewList.append(str(key)+":"+str(tags[key]))
            #Brick Added
	    for tag in toBeIncluded:
		if(name == tag['value']):
			print "Sappy"
			pass
		else:
			tempsense = Sensor.objects(name=tag['value']).first()
			#print 'name is', tag['value']
			if tempsense:
		  		for oldtag in tempsense.tags:
					if(oldtag.name == tag['name']):
							#print oldtag.name, tag['name'], "NEW Name"
							#print oldtag.value, tag['value'], "New Value"
							check = 0
							for agag in tags_owned:
								thename = agag['name']
								thevalue = agag['value']
								if(thename == oldtag.name and thevalue == oldtag.value):
									check = 1
							if(check == 0):
								tags_owned.append(oldtag)
							toBeIncluded.append(oldtag)

	    print tags_owned, "PASSSS", name
	    Sensor.objects(name=name).update(set__tags=tags_owned)
#       payload = {'data':[{
   #             'name': tagname,
  #              'value': tagvalue
 #           },{
#               'name':tagname2,
#               'value':tagvalue2}]}
#       SearchService.post(payload.json())
#       SensorTagService.post('newname')
	    for BrickTag in tobeSearched.keys():
			print [BrickTag+":"+name], "First"
			args = {}
			payload = {'data':[{'name':BrickTag, 'value':name}]}
			form_query('tags', [BrickTag+":"+name], args, '$and')
			print args, "second"
			foundsensors = Sensor._get_collection().find(args)
			print foundsensors, "2.5"
		#	foundsensors = create_response(foundsensors)
			print foundsensors, "third"
        		temps = foundsensors.skip(0).limit(50)
			Values = tobeSearched[BrickTag]
			for subject in temps:
				print subject, "new"
				if subject['name'] not in Recursedict:
					Recursedict[subject['name']]  = list()
				for value in Values:
					if value not in Recursedict[subject['name']]:
						Recursedict[subject['name']].append({'name': BrickTag, 'value':value})
				for tag in subject['tags']:
					Recursedict[subject['name']].append( {'name': tag['name'], 'value': tag['value']})
					#payload = {'data': [{'sensor_id':subject['name']}, {'name': BrickTag, 'value':value},{'name':'RecursiveTag', 'value':subject['name']}]}
			#		print json.dumps(payload).get_json(), "REVERSE REVERSE"
				#	print json.dumps(payload)
				#	self.post(json.dumps(payload))
			#Search for BrickTag:name
			
			#For each value found, run this update function with that tag as the tag to be updated. 
            r.delete(name) #Question
	    Recursedict.pop(name)
         else:
          return jsonify(responses.ds_error)
        return jsonify(responses.success_true)
