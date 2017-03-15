"""
DataService.rest_api.sensor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles interacting with the underlying BrickType models.
It handles the common services for BrickType, such as making a new one or
retrieving BrickType details. It manages the underlying cache, and will
ensure that the cache gets updated as needed.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

import sys
from flask import request, jsonify
from flask.views import MethodView
from .. import responses
from ...models.cs_models import BrickType
from uuid import uuid4
from ... import r,oauth
from ..helper import get_email,xstr,get_building_choices
from ...auth.access_control import authenticate_acl
from ...rpc import defs

class BrickTypeService(MethodView):

    @oauth.require_oauth()
    def get(self,name):
        """
        Retrieve BrickType details based on uuid specified

        Args as data:
        name : <name of BrickType>

        Returns (JSON):
        {
        	name:NameOfBrickType
		subClass: list of subclasses
		superClass: list of superclasses
	}

        """
        if name is None:
            return jsonify(responses.missing_parameters)
        btype = BrickType.objects(name=name).first()
        if btype is None:
            return jsonify(responses.invalid_uuid)
        Subdata = [{value}  for value in btype.subClass]
	Superdata = [{value} for value in btype.SuperClass]
	EquivData = [{value} for value in btype.equivalentClass]	
        response = dict(responses.success_true)
	print "a"
        response.update({'name': str(btype.name),
                        'subClass': 'a',
                        'SuperClass': 'b',
			'equivalentClass': 'c'
                        })
        return jsonify(response)

    @oauth.require_oauth()
    def post(self):
        """
        Creates BrickType

        Args as data:
        "name":<name-of-sensor>

        Returns (JSON) :
        {
            "success": <True or False>
            "uuid" : <name of bricktype if created>
            "error": <details of an error if it happends>
        }
        """
        data = request.get_json()['data']
        try:
	    Brickname = data['name'] #
        except KeyError:
            return jsonify(responses.missing_parameters)
      #  sensor_name = data.get('name') #
        email = get_email()
	subclasses = []
	superClass = []
	equivClass = []
	domain = []
	aType = []
	aInverseOf = []
	aOnProperty = []
	aRange = []
	aSubPropertyOf = []
	aSuperPropertyOf = []
	aSomeValuesFrom = []
	aUsesTag = []
	aLabel = []
	aComment = []
	aisHierarchical = []
	try:	
		subclasses = data.get('subClass')
	except KeyError:
		subclasses = []
	try:
		superClass= data.get('superClass')
	except KeyError:
		superClass = []
	try:
		equivClass = data.get('equivalentClass')
	except KeyError:
		equivClass = []
	try:
		domain = data.get('Domain')
	except KeyError:
		domain = []
	try:
		aType = data.get('Type')
	except KeyError:
		aType = []
	try:
		aInverseOf=data.get('InverseOf')
	except KeyError:
		aInverseOf = []
	try:
		aOnProperty = data.get('onproperty')
	except KeyError:
		 aOnProperty = []
	try:		
		aRange = data.get('Range')
	except KeyError:
		aRange = []
	try:	
		aSubPropertyOf = data.get('subpropertyOf')
	except KeyError:
		aSubPropertyOf = []
	try:
		aSuperPropertyOf= data.get('SuperPropertyOf')
	except KeyError:
		aSuperPropertyOf = []
	try:
		aSomeValuesFrom = data.get('SomeValuesFrom')
	except KeyError:
		aSomeValuesFrom = []
	try:
		aUsesTag = data.get('UsesTag')
	except KeyError:
		aUsesTag = []
	try:
		aLabel = data.get('UsesTag')
	except KeyError:
		aLabel = []
	try:
		aImports = data.get('Imports')
	except KeyError:
		aImports =[]
	try:
		aComment = data.get('Comment')
	except KeyError:
		aComment = []
	try:
		aisHierarchical = data.get('isHierarchical')
	except KeyError:
		aisHierarchical = []
	#building = "Doom"
        #if building in get_building_choices()[0]:
         #   Extrauuid = str(uuid4()) #
	  #  uuid = Brickname #
           # if defs.create_sensor(uuid,email,building):
        BrickType(name=Brickname,
		       subClass = subclasses,
		       SuperClass = superClass,
		       equivalentClass = equivClass,
		       Domain = domain,
		       Type = aType,
		       InverseOf = aInverseOf,
		       OnProperty=aOnProperty,
		       Range = aRange,
		       SubPropertyOf=aSubPropertyOf,
		       SuperPropertyOf=aSuperPropertyOf,
		       SomeValuesFrom=aSomeValuesFrom,
		       UsesTag = aUsesTag,
		       Label = aLabel,
		       Imports = aImports,
		       Comment = aComment,
		       isHierarchical = aisHierarchical).save()
        r.set('owner:{}'.format(Brickname), email)
        response = dict(responses.success_true)
        response.update({'name':Brickname})
        return jsonify(response)

