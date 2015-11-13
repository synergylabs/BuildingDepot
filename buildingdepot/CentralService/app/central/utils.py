from ..models.cs_models import TagType


def get_choices(cls):
    names = [obj['name'] for obj in cls._get_collection().find({}, {'_id': 0, 'name': 1})]
    return zip(names, names)


graph = {tag_type.name: tag_type.children for tag_type in TagType.objects}


def get_all_descendants(name):
    res = []
    for child in graph[name]:
        res.append(child)
        res.extend(get_all_descendants(child))
    return res


def get_tag_descendant_pairs():
    res = {name: get_all_descendants(name) for name in graph}
    return res


