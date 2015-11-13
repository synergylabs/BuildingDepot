from models import Building, Domain


class DomainService(object):

    collection = Domain._get_collection()

    def create_domain(self, building, name):
        domain = {
            Domain.NAME: name,
            Domain.BUILDING: building,
            Domain.NODES: []
        }
        self.collection.insert(domain)

    def retrieve_domain(self, building, name):
        return self.collection.find_one(
            {Domain.NAME: name, Domain.BUILDING: building},
            {'_id': 0}
        )

    def exists_domain(self, building, name):
        return self.retrieve_domain(building, name) is not None
