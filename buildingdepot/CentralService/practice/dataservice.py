from node_service import NodeService
from mongoengine import connect


class DataService(object):

    node_service = NodeService()

    def get(self, building, domain, path):
        path = path.split('/')
        query = None if len(path) % 2 == 0 else path.pop()
        if not path:
            return self.node_service.list_node(building, domain, query)

        pairs = zip(path[::2], path[1::2])

        start = pairs[0]
        node = self.node_service.retrieve_node(building, domain, start[0], start[1])
        if not node:
            return False

        idx = 1
        while idx < len(pairs):
            child = pairs[idx]
            key = child[0] + str(child[1])
            children = [elem['name']+elem['tag'] for elem in node['children']]
            if key not in children:
                return False
            node = self.node_service.retrieve_node(building, domain, child[0], child[1])
            idx += 1

        if not query:
            return node
        else:
            return [elem for elem in node['children'] if elem['name'] == query]


def main():
    connect('tumblelog')
    data_service = DataService()
    # print data_service.get('CSE', 'Location', 'Floor')
    print data_service.get('CSE', 'Location', 'Floor/2')

main()

