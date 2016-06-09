"""
CentralService.rest_api.helper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains all the helper functions needed for the api's
such as conversion of timestamps, strings etc.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""
from ..models.cs_models import TagType

def add_delete(old,now):
    old, now = set(old), set(now)
    return now - old, old - now

def xstr(s):
    """Creates a string object, but for null objects returns
    an empty string
    Args as data:
        s: input object
    Returns:
        object converted to a string
    """
    if s is None:
        return ""
    else:
        return str(s)

def gen_update(params,data):
    """Takes in a list of params and searches for those
       in the data dict. Forms a resultant dict that has
       only those terms.
       Arg as data:
           params: list of params that can be accpeted
           data: the data sent by the user
       Returns:
           dict containing only keys that were available
           in the params list
    """
    result = {}
    for key,value in data.iteritems():
        if key in params:
            result[key] = value
    return result
