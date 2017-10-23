"""
DataService
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Initializes the flask app using the configuration specified in the
config file or falls back to the default one.


@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

import os
from app import create_app
from flask.ext.script import Manager, Shell, Server
from app.rest_api.register import register_view

app = create_app(None)
manager = Manager(app)
register_view(app)

def make_shell_context():
    return dict(app=app)

def get_current():
    return app

port = app.config['SERVER_PORT']
host = '0.0.0.0'

server = Server(host=host, port=port)
manager.add_command('runserver', server)
manager.add_command("shell", Shell(make_context=make_shell_context))

if __name__ == '__main__':
    manager.run(default_command='runserver')
