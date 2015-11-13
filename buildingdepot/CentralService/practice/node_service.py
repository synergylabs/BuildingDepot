from models import Node, Domain
from domain_service import DomainService
from building_service import BuildingService
from mongoengine import connect


class NodeService(object):

    collection = Domain._get_collection()

    def retrieve_node(self, building, domain, name, tag):
        return self.collection.find_one(
            {Domain.NAME: domain, Domain.BUILDING: building},
            {Domain.NODES: {'$elemMatch': {Node.NAME: name, Node.TAG: tag}}, '_id': 0}
        )[Domain.NODES][0]

    def list_node(self, building, domain, name):
        res = self.collection.aggregate([
            {'$unwind': '$nodes'},
            {'$match': {Domain.BUILDING: building, Domain.NAME: domain, 'nodes.name': name}},
            {'$project': {Domain.NODES: 1, '_id': 0}}
        ])['result']

        return [node[Domain.NODES] for node in res]

    def create_node(self, building, domain, name, tag, parent_name=None, parent_tag=None):
        node = {
            Node.NAME: name,
            Node.TAG: tag,
            Node.CHILDREN: []
        }
        self.collection.update(
            {Domain.NAME: domain, Domain.BUILDING: building},
            {'$addToSet': {Domain.NODES: node}}
        )

        if not parent_name:
            return

        node.pop(Node.CHILDREN)
        self.collection.update(
            {Domain.NAME: domain, Domain.BUILDING: building,
             Domain.NODES: {'$elemMatch': {Node.NAME: parent_name, Node.TAG: parent_tag}}},
            {'$addToSet': {'nodes.$.children': node}}
        )


def main():
    connect('tumblelog')
    domain_service = DomainService()
    node_service = NodeService()
    building_service = BuildingService()

    building_service.create_building('CSE')
    domain_service.create_domain('CSE', 'Location')
    node_service.create_node('CSE', 'Location', 'Floor', '1')
    node_service.create_node('CSE', 'Location', 'Area', '1', 'Floor', '1')
    node_service.create_node('CSE', 'Location', 'Floor', '2')
    node_service.create_node('CSE', 'Location', 'Area', '2', 'Floor', '1')
    node_service.create_node('CSE', 'Location', 'Room', '1', 'Area', '1')

# main()