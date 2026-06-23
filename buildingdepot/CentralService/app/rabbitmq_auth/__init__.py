"""RabbitMQ HTTP auth backend.

Lets RabbitMQ authenticate and authorize clients with a BuildingDepot OAuth
token instead of a broker password. The rabbitmq_auth_backend_http plugin POSTs
to the four endpoints below, and each replies with the literal text "allow" or
"deny" by reusing BD's own token validation (user_for_token) and per-sensor ACL
(permission). One token, one authority: BD.

Only token-bearing consumers reach these routes. Internal users (the bdadmin
publisher and ops) authenticate via RabbitMQ's own internal backend and are
never sent here.

Wiring lives in docker/rabbitmq.conf. Design and rationale in
docs/rabbitmq-auth.md.
"""

from flask import Blueprint, request

from ..auth.access_control import permission
from ..rest_api.helper import user_for_token

rabbitmq_auth = Blueprint("rabbitmq_auth", __name__)

# DataService publishes live sensor data here, keyed by sensor_id.
LIVE_EXCHANGE = "master_exchange"
# permission() levels that include read access.
READ_LEVELS = {"r/w/p", "r/w", "r"}


def _reply(allowed):
    return ("allow" if allowed else "deny"), 200, {"Content-Type": "text/plain"}


@rabbitmq_auth.route("/user", methods=["POST"])
def user():
    """Authenticate. The password is a BD token; bind the connection's username
    to the token's real owner so later resource/topic checks can trust it."""
    username = request.form.get("username", "")
    email = user_for_token(request.form.get("password", ""))
    return _reply(email is not None and email == username)


@rabbitmq_auth.route("/vhost", methods=["POST"])
def vhost():
    return _reply(request.form.get("vhost") == "/")


@rabbitmq_auth.route("/resource", methods=["POST"])
def resource():
    """Consumers read the live exchange and manage their own transient
    subscription queues. Publishing and declaring are left to the internal
    user, so any other resource access is denied here."""
    res = request.form.get("resource")
    name = request.form.get("name")
    perm = request.form.get("permission")
    if res == "queue":
        return _reply(True)
    if res == "exchange" and name == LIVE_EXCHANGE:
        return _reply(perm == "read")
    return _reply(False)


@rabbitmq_auth.route("/topic", methods=["POST"])
def topic():
    """The per-sensor gate. A routing_key is a sensor_id, which is the
    Sensor.name in BD, so we allow a read only when BD's ACL grants this user
    read on that sensor."""
    if (
        request.form.get("permission") != "read"
        or request.form.get("name") != LIVE_EXCHANGE
    ):
        return _reply(False)
    email = request.form.get("username", "")
    routing_key = request.form.get("routing_key", "")
    return _reply(permission(routing_key, email=email) in READ_LEVELS)
