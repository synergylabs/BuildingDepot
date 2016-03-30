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
from flask.ext.script import Manager, Shell
import logging
from logging.handlers import RotatingFileHandler

app = create_app(os.getenv('FLASK_CONFIG') or 'dev')
manager = Manager(app)

handler = RotatingFileHandler('debug.log', maxBytes=1000000, backupCount=1)
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)

def make_shell_context():
    return dict(app=app)

def get_current():
    return app

manager.add_command("shell", Shell(make_context=make_shell_context))

if __name__ == '__main__':
    manager.run()
