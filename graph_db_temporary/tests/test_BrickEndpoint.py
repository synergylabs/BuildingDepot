import os
import logging
import requests
from rdflib import Graph, compare
from graph_db_wrapper.brickEndpoint import BrickEndpoint

log = logging.getLogger()
log.setLevel(logging.DEBUG)

def test_basic():
    defaultGraph = 'http://www.xyz.abc/test_basic'
    ep = BrickEndpoint('http://localhost:8890/sparql',
                       '1.0.3',
                       defaultGraph)
    ep.dropGraph(defaultGraph, force=True)

    ep.listGraphs()
    ep.loadFileViaURL(ep.Brick)
    ep.dropGraph(ep.Brick, force=True)

    # load all schema files
    ep.loadSchema()
    ep.listGraphs()

    ep.createGraph('http://abc.efg')
    ep.loadFileViaURL(ep.Brick, graphName='http://abc.efg')
    ep.listGraphs()
    ep.dropGraph('http://abc.efg')
    ep.dropGraph(defaultGraph, force=True)
    ep.listGraphs()


def test_loadGraph():
    defaultGraph = 'http://www.xyz.abc/test_loadGraph'
    ep = BrickEndpoint('http://localhost:8890/sparql',
                       '1.0.3',
                       defaultGraph)
    ep.dropGraph(defaultGraph, force=True)

    g = Graph()
    g.parse('tests/data/sample_graph.ttl', format='turtle')
    ep.loadGraph(g, defaultGraph)
    resultG = ep.queryGraph(defaultGraph, verbose=True)
    assert compare.isomorphic(g, resultG), 'loaded graph and query result not match'

    ep.dropGraph(defaultGraph, force=True)


def test_loadFileViaURL():
    defaultGraph = 'http://www.xyz.abc/test_loadFileViaURL'
    ep = BrickEndpoint('http://localhost:8890/sparql',
                       '1.0.3',
                       defaultGraph)
    ep.dropGraph(defaultGraph, force=True)

    ep.loadFileViaURL(ep.Brick, graphName=defaultGraph)
    resultG = ep.queryGraph(defaultGraph)

    # download the file and read in to compare
    r = requests.get(ep.Brick, allow_redirects=True)
    open('Brick.ttl', 'wb').write(r.content)
    g = Graph()
    g.parse('Brick.ttl', format='turtle')
    assert compare.isomorphic(g, resultG), 'loaded graph and query result not match'

    ep.dropGraph(defaultGraph, force=True)
    os.remove('Brick.ttl')


def test_execUpdate():
    defaultGraph = 'http://www.xyz.abc/test_execUpdate'
    ep = BrickEndpoint('http://localhost:8890/sparql',
                       '1.0.3',
                       defaultGraph)
    ep.dropGraph(defaultGraph, force=True)

    # insert two triples
    q = """
    INSERT
    { <http://x.y.z/subject> rdfs:type rdfs:Literal .
    <http://x.y.z/subject> rdfs:label "XYZ"@en . }
    """
    ep.execUpdate(q)
    count = ep.queryGraphCount(defaultGraph)
    assert int(count) == 2, "unexpected # of triples"

    # update a triple
    q = """
    DELETE
    { <http://x.y.z/subject> rdfs:label "XYZ"@en }
    INSERT
    { <http://x.y.z/subject> rdfs:label "abc"@en }
    """
    ep.execUpdate(q)

    # query and compare
    q = """
    SELECT * WHERE { ?s rdfs:label ?o }
    """
    result = ep.execQuery(q)
    objValue = result['results']['bindings'][0]['o']['value']
    assert objValue == 'abc', "unexpect object value"

    # delete a triple and check count
    q = """
    DELETE { <http://x.y.z/subject> rdfs:label "abc"@en }
    """
    ep.execUpdate(q)
    count = ep.queryGraphCount(defaultGraph)
    assert int(count) == 1, "unexpected # of triples"

    ep.dropGraph(defaultGraph, force=True)


def test_namespace():
    defaultGraph = 'http://www.xyz.abc/test_namespace'
    ep = BrickEndpoint('http://localhost:8890/sparql',
                       '1.0.3',
                       defaultGraph)
    ep.dropGraph(defaultGraph, force=True)

    ep.addNamespace('xyz', 'http://x.y.z/')

    # insert two triples using prefix
    q = """
    INSERT
    { xyz:subject rdfs:type rdfs:Literal .
    xyz:subject rdfs:label "XYZ"@en . }
    """
    ep.execUpdate(q)
    count = ep.queryGraphCount(defaultGraph)
    assert int(count) == 2, "unexpected # of triples"

    # update a triple using mix of prefix and full path
    q = """
    DELETE
    { xyz:subject rdfs:label "XYZ"@en }
    INSERT
    { <http://x.y.z/subject> rdfs:label "abc"@en }
    """
    ep.execUpdate(q)

    # query and compare
    q = """
    SELECT * WHERE { ?s rdfs:label ?o }
    """
    result = ep.execQuery(q)
    objValue = result['results']['bindings'][0]['o']['value']
    assert objValue == 'abc', "unexpect object value"

    # delete a triple and check count
    q = """
    DELETE { xyz:subject rdfs:label "abc"@en }
    """
    ep.execUpdate(q)
    count = ep.queryGraphCount(defaultGraph)
    assert int(count) == 1, "unexpected # of triples"

    ep.dropGraph(defaultGraph, force=True)
