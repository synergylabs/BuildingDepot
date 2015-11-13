from models import Building


class BuildingService(object):

    collection = Building._get_collection()

    def create_building(self, name):
        building = {
            Building.NAME: name,
            Building.DOMAINS: []
        }
        self.collection.insert(building)

    def remove_building(self, name):
        self.collection.remove({Building.NAME: name})

    def retrieve_building(self, name):
        self.collection.find_one(
            {Building.NAME: name},
            {'_id': 0}
        )
