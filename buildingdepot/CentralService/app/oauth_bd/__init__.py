from flask import Blueprint

oauth_bd = Blueprint("oauth_bd", __name__)

from . import views
