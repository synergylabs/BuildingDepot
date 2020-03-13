import os
import requests
from rdflib import Graph, Literal, BNode, URIRef, compare
from SPARQLWrapper import SPARQLWrapper
from SPARQLWrapper import JSON, DIGEST, POST

# Demonstrate grap db operations via SPARQLWrapper.
# The ops here need permissions granted to "sparql" by virtuoso db 6.1.
# But special permissions are not needed by virtuoso db 7.2.5.
# See README.md for details.

defaultGraph = 'http://www.xyz.abc/graph'
brickFile =  'https://brickschema.org/schema/1.0.3/Brick.ttl'  # also serves as graph name
sampleGraphFile = 'sample_graph.ttl'

def getSparql(graphName=None, update=False):
    graph = graphName if graphName else defaultGraph
    #print('get sparql', graph)
    sparql = SPARQLWrapper(endpoint='http://localhost:8890/sparql',
                           updateEndpoint='http://localhost:8890/sparql-auth',
                           defaultGraph=graph)
    sparql.setCredentials('dba', os.environ['DBA_PASSWORD'])
    sparql.setHTTPAuth(DIGEST)
    sparql.setReturnFormat(JSON)
    if update:
        sparql.setMethod(POST)
    return sparql


def queryGraphCount(graphName=None):
    nTriples = None

    sparql = getSparql(graphName=graphName)

    # cheap op: get count
    q = 'SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o . }'
    sparql.setQuery(q)
    ret = sparql.query().convert()
    for r in ret['results']['bindings']:
        nTriples = r['count']['value']
        break
    return nTriples


def queryGraph(graphName=None, verbose=False):
    sparql = getSparql(graphName=graphName)
    sparql.setQuery('SELECT * WHERE { ?s ?p ?o. }')
    ret = sparql.query().convert()
    triples = ret['results']['bindings']
    print(f'queryGraph # of triples:', len(triples))

    g = Graph()
    for r in triples:
        if verbose:
            print(f"({r['s']['type']})<{r['s']['value']}> " \
                  f"({r['p']['type']})<{r['p']['value']}> " \
                  f"({r['o']['type']})<{r['o']['value']}>")

        triple = ()
        for term in (r['s'], r['p'], r['o']):
            if term['type'] == 'uri':
                triple = triple + (URIRef(term['value']),)
            elif term['type'] == 'literal':
                if term['xml:lang']:
                    triple = triple + (Literal(term['value'], term['xml:lang']),)
                else:
                    triple = triple + (Literal(term['value']),)
            elif term['type'] == 'bnode':
                triple = triple + (BNode(term['value']),)
                hasBnode = True
            else:
                assert False, f"term type {term['type']} is not handled"

        g.add(triple)

    return g

def deleteGraph(graphName, force=False):
    try:
        sparql = getSparql(graphName=graphName, update=True)
        if force:
            q = f"DROP SILENT GRAPH <{graphName}>"
        else:
            q = f"DROP GRAPH <{graphName}>"
        print(q)
        sparql.setQuery(q)
        results = sparql.query()
    except Exception as e:
        print(f"deleteGraph exception {e}")


def createGraph(graphName):
    try:
        sparql = getSparql(graphName=graphName, update=True)
        q = f"CREATE GRAPH <{graphName}>"
        print(q)
        sparql.setQuery(q)
        results = sparql.query()
    except Exception as e:
        print(f"createGraph exception {e}")


def loadFileViaURL(graphFile, graphName=None):
    graph = graphName if graphName else graphFile
    try:
        sparql = getSparql(graphName=graph, update=True)
        q = f"LOAD <{graphFile}> INTO <{graph}>"
        print(q)
        sparql.setQuery(q)
        results = sparql.query()
    except Exception as e:
        print(f"loadFileViaURL exception {e}")


# CAUTION: With blank nodes in the graph parsed from a .ttl file, the database side
# loading method loadViaURL should be used,
# That is because the database makes no guarantee the Bnode names will be kept
# consistent across multiple INSERT queries.
# When the file is large, even if the caller of SPARQLWrapper inserts all triples
# with one query SPARQLWrapper may still devide the inserts into batches and thus
# break the bnode name consistency.
def loadGraph(g, graphName):
    sparql = getSparql(graphName=graphName, update=True)

    try:
        sparql = getSparql(graphName=graphName, update=True)
        # q = f"WITH <{graphName}> INSERT {{\n"
        q = f"INSERT {{\n"
        for (s, p, o) in g:
            q += ' '.join([term.n3() for term in (s, p, o)]) + ' .\n'
        q += '}'
        sparql.setQuery(q)
        results = sparql.query()
    except Exception as e:
        print(f"loadGraph exception {e}")


def listGraphs():
    dbGraphs = []
    sparql = getSparql()
    sparql.setQuery('SELECT DISTINCT ?g WHERE { GRAPH ?g {?s a ?t} }')
    results = sparql.query().convert()['results']['bindings']
    print('# of graphs:', len(results))
    for r in results:
        graphName = r['g']['value']
        print(graphName, queryGraphCount(graphName=graphName))
        dbGraphs.append(graphName)
    return dbGraphs

def execQuery(queryStr, graphName=None):
    print(queryStr)
    sparql = getSparql(graphName=graphName)
    sparql.setQuery(queryStr)
    return sparql.query().convert()

def execUpdate(queryStr, graphName=None):
    sparql = getSparql(graphName=graphName, update=True)
    sparql.setQuery(queryStr)
    return sparql.query().convert()


# test body

listGraphs()
deleteGraph(brickFile, force=True)
deleteGraph(defaultGraph, force=True)
listGraphs()

# explicitly created graphs can be deleted without "DROP SILENT"
createGraph(brickFile)
createGraph(defaultGraph)

# load brick schema into graph named itself and into default graph
loadFileViaURL(brickFile)
loadFileViaURL(brickFile, graphName=defaultGraph)

# delete graphs without "DROP SILENT"
listGraphs()
deleteGraph(brickFile)
deleteGraph(defaultGraph)

# parse a SMALL .ttl file, load as tripls, query and compare
g = Graph()
g.parse(sampleGraphFile, format='turtle')
loadGraph(g, defaultGraph)
resultG = queryGraph(defaultGraph, verbose=True)
print('compare db graph and local:', compare.isomorphic(g, resultG))
listGraphs()

deleteGraph(defaultGraph, force=True)
listGraphs()

# load a file via URL, query.  parse the same file into graph and compare.
loadFileViaURL(brickFile)
resultG = queryGraph(brickFile)
r = requests.get(brickFile, allow_redirects=True)
open('Brick.ttl', 'wb').write(r.content)
g = Graph()
g.parse('Brick.ttl', format='turtle')
print('compare db graph and local:', compare.isomorphic(g, resultG))
deleteGraph(brickFile, force=True)
listGraphs()

print('insert 2 triples')
q = """
INSERT
{ <http://x.y.z/subject> rdfs:type rdfs:Literal .
  <http://x.y.z/subject> rdfs:label "XYZ"@en . }
"""
execUpdate(q)
resultG = queryGraph()
print('graph with 2 triples:\n', resultG.serialize(format='ttl').decode('utf-8'))

print('update a triple -- delete and insert')
q = """
DELETE
{ <http://x.y.z/subject> rdfs:label "XYZ"@en }
INSERT
{ <http://x.y.z/subject> rdfs:label "abc"@en }
"""
execUpdate(q)
resultG = queryGraph(defaultGraph, verbose=True)
print('graph after update:', resultG.serialize(format='ttl').decode('utf-8'))

# test execQuery()
print('query graph')
q = """
SELECT * WHERE { ?s rdfs:label ?o }
"""
result = execQuery(q)
print(result)

print('delete a triple')
q = """
DELETE { <http://x.y.z/subject> rdfs:label "abc"@en }
"""
execUpdate(q)
resultG = queryGraph(defaultGraph, verbose=True)
print('graph after delete:', resultG.serialize(format='ttl').decode('utf-8'))

# Empty the default graph
deleteGraph(defaultGraph, force=True)
listGraphs()
exit()
