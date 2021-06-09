"""
CentralService
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Initializes the flask app using the configuration specified in the
config file or falls back to the default one.


@copyright: (c) 2021 SynergyLabs
@license: CMU License. See License file for details.
"""

import os

from .app import create_app
from .app.models.cs_models import User
from .app.rest_api.register import register_view

app = create_app(os.getenv("FLASK_CONFIG") or "dev")
register_view(app)


@app.shell_context_processor
def make_shell_context():
    return dict(app=app, User=User)


if __name__ == "__main__":
    app.run()
