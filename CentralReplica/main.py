from SimpleXMLRPCServer import SimpleXMLRPCServer
from SocketServer import ThreadingMixIn
from models import *
from mongoengine import connect
from config import Config


connect(Config.MONGODB_DATABASE,
        host=Config.MONGODB_HOST,
        port=Config.MONGODB_PORT)


class ThreadXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass


def get_user(email, password):
    user = User.objects(email=email).first()
    if user is not None and user.verify_password(password):
        return True
    return False


def get_building_choices(dataservice_name):
    buildings = DataService.objects(name=dataservice_name).first().buildings
    return zip(buildings, buildings)


def get_building_tags(building):
    tags = Building._get_collection().find({'name': building}, {'tags.name': 1, 'tags.value': 1, '_id': 0})[0]['tags']
    res = {}
    for tag in tags:
        if tag['name'] in res:
            res[tag['name']].append(tag['value'])
        else:
            res[tag['name']] = [tag['value']]
    return res


def validate_users(emails):
    print emails
    for email in emails:
        if User.objects(email=email).first() is None:
            return False
    return True


def get_permission(sensor_tags, building, user_email):
    user = User.objects(email=user_email).first()
    if building not in user.buildings:
        return 'undefined'
    building_permission = {pair.building: Role.objects(name=pair.role).first().permission
                           for pair in user.role_per_building}

    user_tags_list = [{'{}:{}'.format(item.name, item.value) for item in items.tags}
                      for items in user.tags_owned if items.building == building]
    for user_tags in user_tags_list:
        if user_tags.issubset(sensor_tags):
            return building_permission[building]
    return 'undefined'


def validate_email_password(email, password):
    user = User.objects(email=email).first()
    if user is None:
        return False
    return user.verify_password(password)


def get_admins(name):
    obj = DataService.objects(name=name).first()
    if obj is None:
        return []
    return list(obj.admins)

svr = ThreadXMLRPCServer(("", 8080), allow_none=True)
svr.register_function(get_user)
svr.register_function(get_building_choices)
svr.register_function(get_building_tags)
svr.register_function(validate_users)
svr.register_function(get_permission)
svr.register_function(validate_email_password)
svr.register_function(get_admins)
svr.serve_forever()