from .. import svr
from ..rest_api.helper import get_ds, get_sg_ds
from ..models.cs_models import DataService
from xmlrpc.client import ServerProxy


def create_sensor(sensor_id, email, building, fields = None, parent = None):
    if not parent:
        svr = get_remote(get_ds(sensor_id, building))
        try:
            svr.create_sensor(sensor_id, email)
        except Exception as e:
            return False
        return True
    else:
        svr = get_remote(get_ds(parent, building))
        try:
            svr.create_sensor(sensor_id, email, fields, parent)
        except Exception as e:
            return False
        return True


def invalidate_sensor(sensor_id):
    svr = get_remote(get_ds(sensor_id))
    try:
        svr.invalidate_sensor(sensor_id)
    except Exception as e:
        return False
    return True


def delete_sensor(sensor_id, parent = None):
    if not parent:
        svr = get_remote(get_ds(sensor_id))
        try:
            svr.delete_sensor(sensor_id)
        except Exception as e:
            return False
        return True
    else:
        svr = get_remote(get_ds(sensor_id))
        try:
            svr.delete_sensor(sensor_id, parent)
        except Exception as e:
            return False
        return True


def create_permission(user_group, sensor_group, email, permission):
    svr = get_remote(get_sg_ds(sensor_group))
    try:
        svr.create_permission(user_group, sensor_group, email, permission)
    except Exception as e:
        return False
    return True


def delete_permission(user_group, sensor_group):
    svr = get_remote(get_sg_ds(sensor_group))
    try:
        svr.delete_permission(user_group, sensor_group)
    except Exception as e:
        return False
    return True


def invalidate_permission(sensor_group):
    svr = get_remote(get_sg_ds(sensor_group))
    try:
        print("Invalidating permission")
        svr.invalidate_permission(sensor_group)
    except Exception as e:
        print(e)
        return False
    return True


def invalidate_user(user_group, email):
    svr = get_remote(get_sg_ds(sensor_group))
    try:
        svr.invalidate_user(usergroup, email)
    except Exception as e:
        return False
    return True


def get_remote(dataservice):
    ds = DataService.objects(name=dataservice).first()
    return ServerProxy("http://" + ds.host + ":" + "8080")
