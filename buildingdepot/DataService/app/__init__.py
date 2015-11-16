from flask import Flask
from config import config
from mongoengine import connect,register_connection
from flask.ext.bootstrap import Bootstrap
from xmlrpclib import ServerProxy
from flask_oauthlib.provider import OAuth2Provider

import redis
from influxdb import InfluxDBClient

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
    connect(app.config['MONGODB_DATABASE'],
            host=app.config['MONGODB_HOST'],
            port=app.config['MONGODB_PORT'])
    register_connection('bd',name='buildingdepot',host='127.0.0.1',port=27017)
 
    from .api_0_0 import api
    api.init_app(app)
    bootstrap.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .service import service as service_blueprint
    app.register_blueprint(service_blueprint, url_prefix='/service')

    from .oauth_bd import oauth_bd as oauth_bd_blueprint
    app.register_blueprint(oauth_bd_blueprint, url_prefix='/oauth')

    return app
