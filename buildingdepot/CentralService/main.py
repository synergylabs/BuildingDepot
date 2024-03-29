"""
CentralService
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Initializes the flask app using the configuration specified in the
config file or falls back to the default one.


@copyright: (c) 2024 SynergyLabs
@license: CMU License. See License file for details.
"""

# This is for BD docker container only

import os
from flask_script import Manager, Shell, Server

from .app import create_app
from .app.models.cs_models import User
from .app.rest_api.register import register_view

app = create_app("deploy")
manager = Manager(app)
register_view(app)


def make_shell_context():
    return dict(app=app, User=User)


if __name__ == "__main__":
    server = Server("0.0.0.0", threaded=True)
    manager.add_command("shell", Shell(make_context=make_shell_context))
    manager.add_command("runserver", server)
    manager.run(default_command="runserver")
