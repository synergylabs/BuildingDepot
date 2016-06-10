"""
DataService.app
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This file creates the following:
- Initiates the connection object to InfluxDB that will be used by
  the DataService

- Initializes the connection to the Redis cache

- Initializes the OAuth2Provider

The flask application is also created here and all the different
services such as the main dataservice,rest_api and oauth service are
registered as blueprints.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask import Flask
from config import config
from mongoengine import connect,register_connection
from flask.ext.bootstrap import Bootstrap
from xmlrpclib import ServerProxy
from flask_oauthlib.provider import OAuth2Provider

import redis

from influxdb import InfluxDBClient

permissions = {"rw": "r/w", "r": "r", "dr": "d/r","rwp":"r/w/p"}

exchange = 'master_exchange'
r = redis.Redis()
influx = InfluxDBClient('localhost', 8086, 'root', 'root', 'buildingdepot')

bootstrap = Bootstrap()
svr = ServerProxy("http://localhost:8080")

oauth = OAuth2Provider()

def create_app(config_mode):
    app = Flask(__name__)
    app.config.from_object(config[config_mode])

    app.debug = True
    app.secret_key = 'secret'

    oauth.init_app(app)

    config[config_mode].init_app(app)

    register_connection(app.config['MONGODB_DS_ALIAS'],
                    name=app.config['MONGODB_DATABASE_DS'],
                    host=app.config['MONGODB_HOST'],
                    port=app.config['MONGODB_PORT'])
    register_connection(app.config['MONGODB_BD_ALIAS'],
                    name=app.config['MONGODB_DATABASE_BD'],
                    host=app.config['MONGODB_HOST'],
                    port=app.config['MONGODB_PORT'])

    bootstrap.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .service import service as service_blueprint
    app.register_blueprint(service_blueprint, url_prefix='/service')

    from .rest_api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app
