from models import DomainType, NodeType
from domaintype_service import DomainTypeService
from mongoengine import connect


class NodeTypeService(object):

    collection = DomainType._get_collection()

    def retrieve_node_type(self, domain_type, name):
        return self.collection.find_one(
            {DomainType.NAME: domain_type},
            {DomainType.NODE_TYPES: {'$elemMatch': {NodeType.NAME: name}}, '_id': 0}
        )[DomainType.NODE_TYPES][0]

    def exists_node_type(self, domain_type, name):
        return self.retrieve_node_type(domain_type, name) is not None

    def create_node_type(self, domain_type, name, parents):
        node_type = {
            NodeType.NAME: name,
            NodeType.PARENTS: parents,
            NodeType.CHILDREN: []
        }
        self.collection.update(
            {DomainType.NAME: domain_type},
            {'$addToSet': {DomainType.NODE_TYPES: node_type}}
        )
        for parent in parents:
            self.collection.update(
                {DomainType.NAME: domain_type, 'node_types.name': parent},
                {'$addToSet': {'node_types.$.children': name}}
            )

    def list_node_types(self, domain_type):
        return self.collection.find_one(
            {DomainType.NAME: domain_type},
            {DomainType.NODE_TYPES: 1, '_id': 0})


def main():
    connect('tumblelog')
    domaintype_service = DomainTypeService()
    nodetype_service = NodeTypeService()

    # domaintype_service.create_domain_type('Location')
    # domaintype_service.create_domain_type('Energy')
    # nodetype_service.create_node_type('Location', 'Floor', [])
    # nodetype_service.create_node_type('Location', 'HVAC', [])
    # nodetype_service.create_node_type('Location', 'Area', ['Floor'])
    # nodetype_service.create_node_type('Location', 'Zone', ['Area', 'HVAC'])

    print nodetype_service.retrieve_node_type('Location', 'Zone')

main()