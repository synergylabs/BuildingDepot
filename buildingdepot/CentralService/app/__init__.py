"""
CentralService.app
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This file creates the following:
- Initializes the LoginManager that will be used for the frontend

-

The flask application is also created here and all the different
services such as the main centralservice,auth service are
registered as blueprints.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

from flask import Flask
from mongoengine import connect
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_oauthlib.provider import OAuth2Provider
from xmlrpclib import ServerProxy
import redis


app = Flask(__name__)
app.config.from_envvar('CS_SETTINGS')
permissions = {"rw": "r/w", "r": "r", "dr": "d/r","rwp":"r/w/p"}

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

bootstrap = Bootstrap()
oauth = OAuth2Provider()
svr = ServerProxy("http://localhost:8080")
r = redis.Redis(host=app.config['REDIS_HOST'],password=app.config['REDIS_PWD'])

def create_app(config_mode): # TODO: remove config_mode

    connect(db=app.config['MONGODB_DATABASE'],
            host=app.config['MONGODB_HOST'],
            port=app.config['MONGODB_PORT'],
            username=app.config['MONGODB_USERNAME'],
            password=app.config['MONGODB_PWD'],
            authentication_source='admin')
    
    login_manager.init_app(app)
    bootstrap.init_app(app)
    oauth.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .central import central as central_blueprint
    app.register_blueprint(central_blueprint, url_prefix='/central')

    from .rest_api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    from .oauth_bd import oauth_bd as oauth_bd_blueprint
    app.register_blueprint(oauth_bd_blueprint, url_prefix='/oauth')

    return app


from .models.cs_models import User


@login_manager.user_loader
def load_user(email):
    return User.objects(email=email).first()
