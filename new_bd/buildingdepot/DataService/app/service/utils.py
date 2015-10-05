from .. import svr
from flask import current_app

PAGE_SIZE = 10


def get_building_choices(dataservice_name):
    return svr.get_building_choices(dataservice_name)


def get_building_tags(building):
    return svr.get_building_tags(building)


def validate_users(emails):
    return svr.validate_users(emails)


def get_add_delete(old, now):
    old, now = set(old), set(now)
    return now - old, old - now


def get_permission(tags, building, user_email):
    return svr.get_permission(tags, building, user_email)


def validate_email_password(email, password):
    return svr.validate_email_password(email, password)


def get_admins():
    return svr.get_admins(current_app.config['NAME'])