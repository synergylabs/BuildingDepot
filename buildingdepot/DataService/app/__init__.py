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
@license: See License file for details.
"""

from flask import Flask
from mongoengine import connect, register_connection
from flask_bootstrap import Bootstrap
from xmlrpclib import ServerProxy
from flask_oauthlib.provider import OAuth2Provider

import redis

from influxdb import InfluxDBClient
import pdb

app = Flask(__name__)
app.config.from_envvar('DS_SETTINGS')
permissions = {"rw": "r/w", "r": "r", "dr": "d/r", "rwp": "r/w/p"}

exchange = 'master_exchange'

influx = InfluxDBClient(app.config['INFLUXDB_HOST'], 
                        app.config['INFLUXDB_PORT'], 
                        app.config['INFLUXDB_USERNAME'],
                        app.config['INFLUXDB_PWD'],
                        app.config['INFLUXDB_DB']
                        )

r = redis.Redis(host=app.config['REDIS_HOST'],password=app.config['REDIS_PWD'])

bootstrap = Bootstrap()
svr = ServerProxy("http://127.0.0.1:8080")

oauth = OAuth2Provider()


def create_app(config_mode):
    global app
    app.debug = True
    app.secret_key = 'secret'

    oauth.init_app(app)

    connect(db=app.config['MONGODB_DATABASE_BD'],
            host=app.config['MONGODB_HOST'],
            port=app.config['MONGODB_PORT'],
            username=app.config['MONGODB_USERNAME'],
            password=app.config['MONGODB_PWD'],
            authentication_source='admin')

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
