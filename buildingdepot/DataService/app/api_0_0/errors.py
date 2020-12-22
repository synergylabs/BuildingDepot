"""
DataService.rest_api.errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Function definitions for various HTTP errors than can be thrown.

@copyright: (c) 2020 SynergyLabs
@license: CMU License. See License file for details.
"""
from flask import jsonify


def bad_request(message):
    response = jsonify({"error": "Bad request", "message": message})
    response.status_code = 400
    return response


def unauthorized(message):
    response = jsonify({"error": "Unauthorized", "message": message})
    response.status_code = 401
    return response


def forbidden(message):
    response = jsonify({"error": "Forbidden", "message": message})
    response.status_code = 403
    return response


def not_exist(message):
    response = jsonify({"error": "Not exists", "message": message})
    response.status_code = 404
    return response


def not_allowed(message):
    response = jsonify({"error": "Not allowed", "message": message})
    response.status_code = 405
    return response


def internal_error(message):
    response = jsonify({"error": "Internal server error", "message": message})
    response.status_code = 500
    return response
