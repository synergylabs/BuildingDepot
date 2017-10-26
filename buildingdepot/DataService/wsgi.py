"""
CentralService
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Initializes the flask app using the configuration specified in the
config file or falls back to the default one.


@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

# This is for BD docker container only

import os
from app import create_app
from flask.ext.script import Manager, Shell, Server
from app.rest_api.register import register_view

app = create_app(os.getenv('FLASK_CONFIG') or 'dev')
manager = Manager(app)
register_view(app)

def make_shell_context():
    return dict(app=app)

def get_current():
    return app

application = app
#server = Server('0.0.0.0', threaded=True)
#manager.add_command("shell", Shell(make_context=make_shell_context))
#manager.add_command('runserver', server)
#manager.run(default_command='runserver')
