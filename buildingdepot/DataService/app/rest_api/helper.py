"""
DataService.rest_api.helper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains all the helper functions needed for the api's
such as conversion of timestamps, strings etc.

@copyright: (c) 2024 SynergyLabs
@license: CMU License. See License file for details.
"""
import json
import pika
import time
from datetime import datetime
from flask import request, abort
from functools import wraps

from .. import exchange, r, rabbitmq_username, rabbitmq_password
from ..models.ds_models import Building, TagType, User
from ..auth.views import Token


def get_email():
    """Returns the email address of the user making the request
    based on the OAuth token
    Args as data:
        None - Get's OAuth token from the request context
    Returns:
        E-mail id of the user making the request
    """
    headers = request.headers
    token = headers["Authorization"][7:]
    user = r.get("".join(["oauth:", token]))
    if user:
        return user
    token = Token.objects(access_token=token).first()
    return token.email


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


def jsonString(obj, pretty=False):
    """Creates a json object, if pretty is specifed as True proper
    formatting is added
    Args as data:
        obj: object that needs to be converted to a json object
        pretty: Boolean specifying whether json object has to be formatted
    Returns:
        JSON object corresponding to the input object
    """
    if pretty == True:
        return json.dumps(obj, sort_keys=True, indent=4, separators=(",", ": ")) + "\n"
    else:
        return json.dumps(obj)


def create_response(sensors):
    """Iterates over the list and generates a json response of sensors list
    Args as data:
        list of sensor retrieved from MongoDB
    Returns:
        {
            List of formatted sensor objects
        }
    """
    sensor_list = []
    for sensor in sensors:
        json_temp = create_json(sensor)
        sensor_list.append(json_temp)
    return sensor_list


def create_json(sensor):
    """Simple function that creates a json object to return for each sensor
    Args as data:
        sensor object retrieved from MongoDB
    Returns:
        {
            Formatted sensor object as below
        }
    """
    json_object = {
        "building": sensor.get("building"),
        "name": sensor.get("name"),
        "tags": sensor.get("tags"),
        "metadata": sensor.get("metadata"),
        "source_identifier": sensor.get("source_identifier"),
        "source_name": sensor.get("source_name"),
    }
    return json_object


def check_if_super(email=None):
    if email is None:
        email = get_email()
    if r.sismember("superusers", email):
        return True
    if User.objects(email=email).first().role == "super":
        r.sadd("superusers", email)
        return True
    return False


def timestamp_to_time_string(t):
    """Converts a unix timestamp to a string representation of the timestamp
    Args:
        t: A unix timestamp float
    Returns
        A string representation of the timestamp
    """
    return (
        time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t)) + str(t - int(t))[1:10] + "Z"
    )


def connect_broker():
    """
    Args:
        None:
    Returns:
        pubsub: object corresponding to the connection with the broker
    """
    try:
        credentials = pika.PlainCredentials(rabbitmq_username, rabbitmq_password)
        parameters = pika.ConnectionParameters(host="localhost", credentials=credentials, connection_attempts=3, retry_delay=5)
        pubsub = pika.BlockingConnection(parameters)
        channel = pubsub.channel()
        channel.exchange_declare(exchange=exchange, exchange_type="direct", durable=True)
        channel.close()
        return pubsub
    except Exception as e:
        print(("Failed to open connection to broker " + str(e)))
        return None


def add_delete_users(old, now):
    user_old, user_new = [], []
    for user in old:
        user_old.append(user["user_id"])
    for user in now:
        user_new.append(user["user_id"])
    old, now = set(user_old), set(user_new)
    return now - old, old - now


def add_delete(old, now):
    old, now = set(old), set(now)
    return now - old, old - now


def form_query(param, values, args, operation):
    res = []
    if param == "tags":
        for tag in values:
            key_value = tag.split(":", 1)
            current_tag = {"tags.name": key_value[0], "tags.value": key_value[1]}
            res.append(current_tag)
    elif param == "metadata":
        for meta in values:
            key_value = meta.split(":", 1)
            current_meta = {"metadata." + key_value[0]: key_value[1]}
            res.append(current_meta)
    else:
        for value in values:
            res.append({param: value})
    if args.get(operation) is None:
        args[operation] = res
    else:
        args[operation] = args.get(operation) + res


def get_building_tags(building):
    """Get all the tags that this building has associated with it"""
    tags = Building._get_collection().find(
        {"name": building}, {"tags.name": 1, "tags.value": 1, "_id": 0}
    )[0]["tags"]
    res = {}
    for tag in tags:
        if tag["name"] in res:
            res[tag["name"]]["values"].append(tag["value"])
        else:
            tagtype_dict = {}
            tagtype_dict["values"] = [tag["value"]]
            tagtype_dict["acl_tag"] = TagType.objects(name=tag["name"]).first().acl_tag
            res[tag["name"]] = tagtype_dict
    return res


def check_oauth(f):
    @wraps(f)
    def secure(*args, **kwargs):
        if not request.headers.get("Authorization"):
            abort(401)
        access_token = request.headers.get("Authorization")[7:]
        if request.headers.get("Authorization") is not None:
            user = r.get("".join(["oauth:", access_token]))
            if user is not None:
                return f(*args, **kwargs)
            else:
                # Not found in Redis, checking in MongoDB
                token = Token.objects(access_token=access_token).first()
                if token:
                    # Calculate time to expire in seconds using timedelta
                    expires_in = (token.expires - datetime.now()).total_seconds()
                    if expires_in > 0:
                        # Still valid, adding to redis
                        r.setex(
                            "".join(["oauth:", access_token]),
                            int(expires_in),
                            token.user,
                        )
                        return f(*args, **kwargs)
                    else:
                        # Invalid, deleting
                        token.delete()
        abort(401)

    return secure
