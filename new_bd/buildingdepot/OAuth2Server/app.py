from datetime import datetime, timedelta
from flask import Flask,current_app,Blueprint
from flask import session, request
from flask import render_template, redirect, jsonify
from werkzeug.security import gen_salt
from flask_oauthlib.provider import OAuth2Provider
from bson.objectid import ObjectId
#from ..models.cs_models import *
import sys
sys.path.append('/srv/buildingdepot/CentralService/app/models')
from cs_models import User
from mongoengine import *
from mongoengine.context_managers import switch_db

connect('buildingdepot',host='127.0.0.1',port=27017)
register_connection('bd',name='buildingdepot',host='127.0.0.1',port=27017)

app = Flask(__name__, template_folder='templates')
app.debug = True
app.secret_key = 'secret'
oauth = OAuth2Provider(app)

class Client(Document):
    client_id = StringField(required=True, unique=True)
    client_secret = StringField(required=True)
    user = ReferenceField(User)
    _redirect_uris = StringField()
    _default_scopes = StringField()

    @property
    def client_type(self):
        return 'public'

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0]

    @property
    def default_scopes(self):
        if self._default_scopes:
            return self._default_scopes.split()
        return []


class Grant(Document):
    user = ReferenceField(User)
    client = ReferenceField(Client)
    code = StringField(required=True)
    redirect_uri = StringField()
    expires = DateTimeField()
    _scopes = StringField()

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


class Token(Document):
    client = ReferenceField(Client)
    user = ReferenceField(User)
    token_type = StringField()
    access_token = StringField(unique=True)
    refresh_token = StringField(unique=True)
    expires = DateTimeField()
    _scopes = StringField()

    meta = {"db_alias": "bd"}
    
    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


def current_user():
    print "Entered current_user()"
    if 'id' in session:
        uid = session['id']
	try:
		return User.objects(id=ObjectId(str(uid))).first()
	except Exception as e:
		return None
    return None

def retrieve_user(user):
	return User.objects(email=user['email']).first()

@app.route('/', methods=('GET', 'POST'))
def home():
    print "Entered route /"
    if request.method == 'POST':
        email = request.form.get('username')
	user = User.objects(email=email).first()
        print "User"
	print Client.objects().first().client_id
	if not user:
            return jsonify({'response': 'Access Denied'})
        session['id'] = str(user['id'])
	return redirect('/')
    user_current = current_user()
    print "Render templated"
    return render_template('home.html', user=user_current)


@app.route('/client')
def client():
    print "Entered route client" 
    user_current = current_user()
    if not user_current:
        return redirect('/')
    item = Client(
	client_id=gen_salt(40), 
	client_secret=gen_salt(50), 
	_redirect_uris=' '.join([
	    'http://localhost:8000/authorized',
	    'http://127.0.0.1:8000/authorized',
            'http://127.0.1:8000/authorized',
     	    'http://127.1:8000/authorized']), 
	_default_scopes='email', 
	user=retrieve_user(user_current)).save()
    return jsonify(
	client_id=item.client_id, 
	client_secret=item.client_secret
    )


@oauth.clientgetter
def load_client(client_id):
    print "Entered load client"
    return Client.objects(client_id=client_id).first()


@oauth.grantgetter
def load_grant(client_id, code):
    print "Entered load grant"
    return Grant.objects(client=Client.objects(client_id=client_id).first(),
	code=code).first()


@oauth.grantsetter
def save_grant(client_id, code, request, *args, **kwargs):
    print "Entered save grant"
    expires = datetime.utcnow() + timedelta(seconds=100)
    grant = Grant(
	client=Client.objects(client_id=client_id).first(),
	code=code['code'], 
	redirect_uri=request.redirect_uri, 
	_scopes=' '.join(request.scopes), 
	user=retrieve_user(current_user()), expires=expires)
    grant.save()
    return grant


@oauth.tokengetter
def load_token(access_token = None, refresh_token = None):
    with switch_db(Token,'bd') as tkn:
	if access_token:
		return tkn.objects(access_token=access_token).first()
    	elif refresh_token:
		return tkn.objects(refresh_token=refresh_token).first()	


@oauth.tokensetter
def save_token(token, request, *args, **kwargs):
    print "Entered save token"
    toks = Token.objects(client=request.client,user=request.user)
    for t in toks:
	t.delete()

    expires_in = token.pop('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=expires_in)
    tok = Token(
	access_token=token['access_token'], 
	refresh_token=token['refresh_token'], 
	token_type=token['token_type'], 
	_scopes=token['scope'], 
	expires=expires, 
	client=request.client, 
	user=request.user).save()
    return tok


@app.route('/oauth/token', methods=['GET', 'POST'])
@oauth.token_handler
def access_token():
    print "Entered access token"
    return None


@app.route('/oauth/authorize', methods=['GET', 'POST'])
@oauth.authorize_handler
def authorize(*args, **kwargs):
    print "Entered authorize handler"
    user = current_user()
    if not user:
        return redirect('/')
    if request.method == 'GET':
        client_current = kwargs.get('client_id')
        client = Client.objects(client_id=client_current).first()
        kwargs['client'] = client
        kwargs['user'] = user
        return render_template('authorize.html', **kwargs)
    confirm = request.form.get('confirm', 'no')
    return confirm == 'yes'


@app.route('/api/me')
@oauth.require_oauth()
def me():
    print "Entered me"
    user = request.oauth.user
    return jsonify(username=user.email, test=1)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
