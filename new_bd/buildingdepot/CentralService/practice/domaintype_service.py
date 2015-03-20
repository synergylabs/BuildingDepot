from models import DomainType


class DomainTypeService(object):

    collection = DomainType._get_collection()

    def create_domain_type(self, name):
        domain_type = {
            DomainType.NAME: name,
            DomainType.NODE_TYPES: []
        }
        return self.collection.insert(domain_type)

    def retrieve_domain_type(self, name):
        return self.collection.find_one(
            {DomainType.NAME: name},
            {'_id': 0}
        )

    def exists_domain_type(self, name):
        self.retrieve_domain_type(name) is not None

    def remove_domain_type(self, name):
        return self.collection.remove({DomainType.NAME: name})