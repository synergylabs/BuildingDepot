from flask import Blueprint

central = Blueprint("central", __name__)

from . import views
