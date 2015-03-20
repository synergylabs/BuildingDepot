from flask.ext.restful import Api, Resource
from flask.ext.httpauth import HTTPBasicAuth
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import g, current_app
from .errors import unauthorized
from ..service.utils import validate_email_password

auth = HTTPBasicAuth()
api = Api(prefix='/api/v0.0')


def verify_auth_token(token):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except:
        return None
    return data['email']


def generate_auth_token(email, expiration):
    s = Serializer(current_app.config['SECRET_KEY'],
                   expires_in=expiration)
    return s.dumps({'email': email})


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@auth.verify_password
def verify_auth(email_or_token, password):
    if email_or_token == '':
        return False
    if password == '':
        email = verify_auth_token(email_or_token)
        if email is not None:
            g.user = email
            g.token_used = True
            return True
        return False

    if not validate_email_password(email_or_token, password):
        return False
    g.user = email_or_token
    g.token_used = False
    return True


class TokenAPI(Resource):
    decorators = [auth.login_required]

    def get(self):
        if g.token_used:
            return unauthorized('Users can only use email and password to get token')
        expires_in = current_app.config['TOKEN_EXPIRATION']
        return {'token': generate_auth_token(g.user, expires_in),
                'expires in': '{} minutes'.format(expires_in/60)}

api.add_resource(TokenAPI,
                 '/token', endpoint='token')

from resources.subscription import Subscription, SubscriptionChanges, SubscriptionClearAllChanges, \
    SubscriptionClearChange
api.add_resource(Subscription,
                 '/subscription/<string:email>', endpoint='subscription')
api.add_resource(SubscriptionChanges,
                 '/subscription/<string:email>/changes', endpoint='subscription_changes')
api.add_resource(SubscriptionClearAllChanges,
                 '/subscription/<string:email>/clearchanges', endpoint='subscription_changes_clear')
api.add_resource(SubscriptionClearChange,
                 '/subscription/<string:email>/clearchanges/<string:sensor_name>', endpoint='subscription_change_clear')

from resources.write import Write
api.add_resource(Write,
                 '/sensor/<string:sensor_name>/timeseries', endpoint='write')

from resources.search import Search
api.add_resource(Search,
                 '/search/sensors', endpoint='search_sensors')