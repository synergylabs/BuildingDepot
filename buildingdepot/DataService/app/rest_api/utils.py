"""
DataService.rest_api.utils
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains all the definitions for the rpc's that are used to talk to the
CentralService. Any query in the CentralService that requires data from the
CentralService such as valid tags, list of buildings etc. will have to go through
this if data is not found in the cache

@copyright: (c) 2024 SynergyLabs
@license: CMU License. See License file for details.
"""

from flask import current_app

from .. import svr

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
    user_old, user_new = [], []
    for user in old:
        user_old.append(user["user_id"])
    for user in new:
        user_new.append(user["user_id"])
    old, now = set(user_old), set(user_new)
    return now - old, old - now


def get_permission(tags, building, user_email):
    return svr.get_permission(tags, building, user_email)


def validate_email_password(email, password):
    return svr.validate_email_password(email, password)


def get_admins():
    return svr.get_admins(current_app.config["NAME"])
