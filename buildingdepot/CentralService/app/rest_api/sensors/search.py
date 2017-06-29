"""
DataService.rest_api.search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles the search functionality, enabling users to
search for Sensors based on a combination of the parameters that
a sensor contains such as Tags,Building,Source identifier,uuid etc.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask import request,jsonify
from flask.views import MethodView
from .. import responses
from ...models.cs_models import Sensor, BrickType
from ..helper import form_query,create_response
from ... import oauth

class SearchService(MethodView):

    @oauth.require_oauth()
    def post(self):
        try:
            data = request.get_json()['data']
        except KeyError:
	    print "UhOh, Search.py"
            return jsonify(responses.missing_data)

        args = {}
	tempargs={}
        for key, values in data.iteritems():
	    tempargs = {}
	    print key, values
	    Special = values[len(values)-1]
	    Special = Special[len(Special)-1:]
	    print Special
	    if Special in ['*', '+', '-']:
		newvalue = values[0]
		newvalue = [newvalue[:len(newvalue)-1]]
		if key == 'Type':
			form_query('Enttype', values, args, "$or")
			if Special == '*' or Special == '+':
				#Traverse Upwards
				loopvar = 1
				tempvalues = [newvalue]
				newTemp = []
				while loopvar==1:
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
				tempvalues = [newvalue]
				newTemp = []
				while loopvar==1:
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
			
		elif key =='Tags':
			form_query('tags',newvalue,args,"$or")
			loopvar = 1
			tempvalues = [newvalue]
			newTemp = []
			Core = newvalue[0].split(':',1)[0]
			while loopvar==1:
				loopvar = 0
				for singleValue in tempvalues:
					form_query('tags', singleValue, tempargs, "$or")
					newCollect = Sensor._get_collection().find(tempargs)
					tempargs = {}
					for newValue in newCollect:
						newName = newValue.get('name')
						newTag = [Core+":"+newName]
						form_query('tags',newTag, args, "$or")
						newTemp.append(newTag)
						loopvar = 1
					tempvalues = newTemp
					newTemp =[]

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
		print values, "NOW"
                form_query('tags',values,args,"$and")
		print args, "AFTER"
            elif key == 'MetaData':
                form_query('metadata',values,args,"$and")
        if not args:
            return jsonify(responses.no_search_parameters)
        collection = Sensor._get_collection().find(args)
        response = dict(responses.success_true)
        response.update({"result":create_response(collection)})
        return jsonify(response)