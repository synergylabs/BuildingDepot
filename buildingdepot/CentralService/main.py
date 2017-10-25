"""
CentralService
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Initializes the flask app using the configuration specified in the
config file or falls back to the default one.


@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

import os
from app import create_app
from app.models.cs_models import User
from flask.ext.script import Manager, Shell, Server
from app.rest_api.register import register_view

app = create_app('deploy')
manager = Manager(app)
register_view(app)

def make_shell_context():
    return dict(app=app, User=User)

server = Server()
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('runserver', server)

if __name__ == '__main__':
    manager.run(default_command='runserver')
