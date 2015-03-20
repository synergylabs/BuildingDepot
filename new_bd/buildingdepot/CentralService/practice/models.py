from mongoengine import *

connect('tumblelog')


class NodeType(EmbeddedDocument):
    NAME = 'name'
    PARENTS = 'parents'
    CHILDREN = 'children'

    name = StringField()
    parents = ListField(StringField())
    children = ListField(StringField())


class DomainType(Document):
    NAME = 'name'
    NODE_TYPES = 'node_types'

    name = StringField()
    node_types = ListField(EmbeddedDocumentField(NodeType))


class NodeChildren(EmbeddedDocument):
    name = StringField()
    tags = ListField(StringField())


class Node(EmbeddedDocument):
    NAME = 'name'
    TAG = 'tag'
    CHILDREN = 'children'

    name = StringField()
    tag = StringField()
    children = ListField(EmbeddedDocumentField(NodeChildren))


class Domain(Document):
    NAME = 'name'
    BUILDING = 'building'
    NODES = 'nodes'

    name = StringField()
    building = StringField()
    nodes = ListField(EmbeddedDocumentField(Node))


class Building(Document):
    NAME = 'name'
    DOMAINS = 'domains'

    name = StringField(max_length=120, required=True)


def create_node(building_name, domain_name, path):
    graph = DomainType._get_collection().find({'name': domain_name}, {'node_types': 1})['node_types']

    graph = {vertex['name']: {
        'parents': vertex['parents'],
        'children': vertex['children']} for vertex in graph}

    elems = path.split('/')
    vertices = elems[::2]
    tags = elems[1::2]

    start = vertices[0]
    if start not in graph:
        raise Exception('Key {} does not exist'.format(start))

    if graph[start]['parents']:
        roots = [node_type for node_type in graph if not graph[node_type]['parents']]
        if not roots:
            raise Exception('No node type associated with the building type')

        roots_str = ' or '.join(roots)
        if len(roots) > 1:
            msg = 'Path should start with the roots {}'.format(roots_str)
        else:
            msg = 'Path should start with the root {}'.format(roots_str)

        raise Exception(msg)

    child_idx = 1
    while child_idx < len(vertices):
        parent, child = vertices[child_idx-1], vertices[child_idx]
        if child not in graph[parent]['children']:
            raise Exception('Key does not exist')
        child_idx += 1



