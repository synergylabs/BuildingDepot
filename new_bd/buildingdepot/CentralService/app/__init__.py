from flask import Flask
from config import config
from mongoengine import connect
from .api_0_0 import api
from flask.ext.login import LoginManager
from flask.ext.bootstrap import Bootstrap

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

bootstrap = Bootstrap()


def create_app(config_mode):
    connect('buildingdepot')
    app = Flask(__name__)
    app.config.from_object(config[config_mode])
    config[config_mode].init_app(app)
    connect(app.config['MONGODB_DATABASE'],
            host=app.config['MONGODB_HOST'],
            port=app.config['MONGODB_PORT'])

    api.init_app(app)
    login_manager.init_app(app)
    bootstrap.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .central import central as central_blueprint
    app.register_blueprint(central_blueprint, url_prefix='/central')

    return app


from .models.cs_models import User


@login_manager.user_loader
def load_user(email):
    return User.objects(email=email).first()