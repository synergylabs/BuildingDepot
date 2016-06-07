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
from app.rest_api.register import register_view
from flask import url_for

app = create_app(os.getenv('FLASK_CONFIG') or 'dev')
manager = Manager(app)
register_view(app)

def make_shell_context():
    return dict(app=app)

def get_current():
    return app

@manager.command
def list_routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():

        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        methods = ','.join(rule.methods)
        url = url_for(rule.endpoint, **options)
        line = urllib.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, url))
        output.append(line)
    
    for line in sorted(output):
        print line

manager.add_command("shell", Shell(make_context=make_shell_context))

if __name__ == '__main__':
    manager.run()
