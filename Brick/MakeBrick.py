import pandas as pd
import operator
import pickle
import shelve
import re
from collections import Counter, defaultdict, OrderedDict, deque
import csv
import rdflib
from rdflib.namespace import OWL, RDF, RDFS
from rdflib import URIRef
import os

def main():
	BRICK = rdflib.Namespace('http://buildsys.org/ontologies/Brick#')
	BRICKFRAME = rdflib.Namespace('http://buildsys.org/ontologies/BrickFrame#')
	GHC = rdflib.Namespace('http://cmu.edu/building/ontology/ghc#')
	newG = rdflib.Graph()
	newG.bind('GHC',GHC)
	newG.bind('brick', BRICK)
	newG.bind('bf',BRICKFRAME)
	newG.parse('BrickFrame.ttl',format='turtle')
	tempdict = dict()
	Relationships = dict()
	for s, p, o in newG:
#		print s, p , o
		if p not in tempdict:
			print p
			tempdict[p] = 1
		if s not in Relationships:
			Relationships[s] = dict()
			Relationships[s][p]= list()
			Relationships[s][p].append(o)
		if p not in Relationships[s]:
			Relationships[s][p] = list()
			Relationships[s][p].append(o)
		else:
			Relationships[s][p].append(o)
	print "break1"
	newG = rdflib.Graph()
	newG.bind('GHC',GHC)
	newG.bind('brick', BRICK)
	newG.bind('bf',BRICKFRAME)
	newG.parse('Brick.ttl',format='turtle')
	for s, p, o in newG:
#		print s,p,o
		if p not in tempdict:
			print p
			tempdict[p] = 1
		if s not in Relationships:
			Relationships[s] = dict()
			Relationships[s][p]= list()
			Relationships[s][p].append(o)
		if p not in Relationships[s]:
			Relationships[s][p] = list()
			Relationships[s][p].append(o)
		else:
			Relationships[s][p].append(o)

	print "break2"
	newG = rdflib.Graph()
	newG.bind('GHC',GHC)
	newG.bind('brick', BRICK)
	newG.bind('bf',BRICKFRAME)
	newG.parse('BrickTag.ttl',format='turtle')
	for s, p, o in newG:
		if p not in tempdict:
			print p
			tempdict[p] = 1
		if s not in Relationships:
			Relationships[s] = dict()
			Relationships[s][p]= list()
			Relationships[s][p].append(o)
		if p not in Relationships[s]:
			Relationships[s][p] = list()
			Relationships[s][p].append(o)
		else:
			Relationships[s][p].append(o)

	Predicates = ['subClass','superClass','equivalentClass','Domain','Type','InverseOf','onProperty','Range','subPropertyOf','SuperPropertyOf','SomeValuesFrom','UsesTag','UsesTag','Imports','Comment','isHierarchical']
	for item in Relationships:
		#Make API Call
		for item in Predicates:

#List
	print len(tempdict.keys())#if("Class" in p):
main()
	#	print s, p, o
