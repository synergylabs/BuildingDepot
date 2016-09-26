from .. import svr
from flask import current_app

PAGE_SIZE = 100


def get_building_choices(dataservice_name):
    return svr.get_building_choices(dataservice_name)


def get_user_oauth(email):
    return svr.get_user_oauth(email)


def get_building_tags(building):
    return svr.get_building_tags(building)


def validate_users(emails, list_format=False):
    return svr.validate_users(emails, list_format)


def get_permission(tags, building, user_email):
    return svr.get_permission(tags, building, user_email)


def validate_email_password(email, password):
    return svr.validate_email_password(email, password)


def get_admins():
    print svr.get_admins(current_app.config['NAME'])
    return svr.get_admins(current_app.config['NAME'])
