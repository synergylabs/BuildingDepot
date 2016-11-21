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
	print "b"
	print response
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
	
	subclasses = data.get('subClass')
	superClass= data.get('superClass')
	equivClass = data.get('equivalentClass')
	domain = data.get('Domain')
	aType = data.get('Type')
	aInverseOf=data.get('InverseOf')
	aOnProperty = data.get('onproperty')
	aRange = data.get('Range')
	aSubPropertyOf = data.get('subpropertyOf')
	aSuperPropertyOf= data.get('SuperPropertyOf')
	aSomeValuesFrom = data.get('SomeValuesFrom')
	aUsesTag = data.get('UsesTag')
	aLabel = data.get('UsesTag')
	aImports = data.get('Imports')
	aComment = data.get('Comment')
	aisHierarchical = data.get('isHierarchical')
	building = "Doom"
	print get_building_choices()
        if building in get_building_choices()[0]:
	    print get_building_choices()
            Extrauuid = str(uuid4()) #
	    uuid = Brickname #
            if defs.create_sensor(uuid,email,building):
		print "happy"
                BrickType(name=uuid,
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
                r.set('owner:{}'.format(uuid), email)
                response = dict(responses.success_true)
                response.update({'uuid':uuid})
                return jsonify("bi")
            else:
                return jsonify("ai")
        return jsonify(get_building_choices())

