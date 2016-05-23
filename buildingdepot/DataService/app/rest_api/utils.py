"""
DataService.rest_api.utils
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains all the definitions for the rpc's that are used to talk to the
CentralService. Any query in the CentralService that requires data from the
CentralService such as valid tags, list of buildings etc. will have to go through
this if data is not found in the cache

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from .. import svr
from flask import current_app

PAGE_SIZE = 100


def get_building_choices(dataservice_name):
    return svr.get_building_choices(dataservice_name)


def get_user_oauth(email):
    return svr.get_user_oauth(email)


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
