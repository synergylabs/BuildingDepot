"""
CentralService.rest_api.helper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains all the helper functions needed for the api's
such as conversion of timestamps, strings etc.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""
from flask import current_app,request
from ..models.cs_models import TagType,DataService,User
from ..models.cs_models import Building,SensorGroup,Sensor
from ..oauth_bd.views import Token
import smtplib,requests,base64
from . import responses

url="https://www.googleapis.com/oauth2/v3/token"
headers = {'content-type': 'application/x-www-form-urlencoded',
                                        'user-agent' : 'BuildingDepot'}

def add_delete(old,now):
    old, now = set(old), set(now)
    return now - old, old - now

def xstr(s):
    """Creates a string object, but for null objects returns
    an empty string
    Args as data:
        s: input object
    Returns:
        object converted to a string
    """
    if s is None:
        return ""
    else:
        return str(s)

def gen_update(params,data):
    """Takes in a list of params and searches for those
       in the data dict. Forms a resultant dict that has
       only those terms.
       Arg as data:
           params: list of params that can be accpeted
           data: the data sent by the user
       Returns:
           dict containing only keys that were available
           in the params list
    """
    result = {}
    for key,value in data.iteritems():
        if key in params:
            result[key] = value
    return result

def send_local_smtp(user_name,to_email,password):
    sender = current_app.config['EMAIL_ID']
    receivers = [to_email]

    message = responses.registration_email%(sender,user_name,to_email,to_email,password)

    try:
       smtpObj = smtplib.SMTP('localhost')
       smtpObj.sendmail(sender, receivers, message)
    except smtplib.SMTPException:
       print "Failed to send registration mail to %s"%(to_email)

def GenerateOAuth2String(username, access_token, base64_encode=True):
    """Generates an IMAP OAuth2 authentication string.

    See https://developers.google.com/google-apps/gmail/oauth2_overview

    Args:
    username: the username (email address) of the account to authenticate
    access_token: An OAuth2 access token.
    base64_encode: Whether to base64-encode the output.

    Returns:
    The SASL argument for the OAuth2 mechanism.
    """
    auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)
    if base64_encode:
        auth_string = base64.b64encode(auth_string)
    return auth_string

def get_access_token():
    params ="client_id="+current_app.config['CLIENT_ID']
    params+="&client_secret="+current_app.config['CLIENT_SECRET']
    params+="&refresh_token="+current_app.config['REFRESH_TOKEN']
    params+="&grant_type=refresh_token"
    try:
        r = requests.post(url,params,headers=headers)
        access_token = r.json()['access_token']
        return access_token
    except Exception as e:
        print "Failed to obtain access token "+str(e)


def send_mail_gmail(user_name,to_email,password):
    print "getting access_token"
    access_token = get_access_token()
    if access_token is None:
        return
    sender = current_app.config['EMAIL_ID']
    print access_token
    print sender
    try:
        smtp_conn = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_conn.ehlo('test')
        smtp_conn.starttls()
        smtp_conn.docmd('AUTH', 'XOAUTH2 ' + base64.b64encode(GenerateOAuth2String(sender,access_token,base64_encode=False)))
        msg = responses.registration_email%(sender,user_name,to_email,to_email,password)
        smtp_conn.sendmail(sender,to_email,msg)
    except Exception as e:
        print "Failed to send registration email to "+to_email+" "+str(e)

def get_email():
    """ Returns the email address of the user making the request
    based on the OAuth token
    Args as data:
        None - Get's OAuth token from the request context
    Returns:
        E-mail id of the user making the request
    """
    headers = request.headers
    token = headers['Authorization'].split()[1]
    return Token.objects(access_token=token).first().email

def check_if_super(email=None):
    if email is None:
        email = get_email()
    if User.objects(email=email).first().role == 'super':
        return True
    return False

def get_building_choices():
    """Get the list of buildings in this DataService"""
    dataservices = DataService.objects()
    buildings_list = []
    for dataservice in dataservices:
        for building in dataservice.buildings:
            print building
            if building not in buildings_list:
                buildings_list.append(building)
    return zip(buildings_list,buildings_list)

def get_building_tags(building):
    """Get all the tags that this building has associated with it"""
    tags = Building._get_collection().find({'name': building}, {'tags.name': 1, 'tags.value': 1, '_id': 0})[0]['tags']
    res = {}
    for tag in tags:
        if tag['name'] in res:
            res[tag['name']]['values'].append(tag['value'])
        else:
            tagtype_dict = {}
            tagtype_dict['values'] = [tag['value']]
            tagtype_dict['acl_tag'] = TagType.objects(name=tag['name']).first().acl_tag
            res[tag['name']] = tagtype_dict
    return res

def form_query(param,values,args,operation):
    res = []
    if param == 'tags':
        for tag in values:
            key_value = tag.split(":", 1)
            current_tag = {"tags.name": key_value[0], "tags.value": key_value[1]}
            res.append(current_tag)
    elif param == 'metadata':
        for meta in values:
            key_value = meta.split(":", 1)
            current_meta = {"metadata."+key_value[0]: key_value[1]}
            res.append(current_meta)
    else:
        for value in values:
            res.append({param:value})
    if args.get(operation) is None:
        args[operation] = res
    else:
        args[operation] = args.get(operation)+res

def create_json(sensor):
    """Simple function that creates a json object to return for each sensor
    Args as data:
        sensor object retrieved from MongoDB
    Returns:
        {
            Formatted sensor object as below
        }
    """
    json_object = {'type':sensor.get('Enttype'),
		   'building': sensor.get('building'),
                   'name': sensor.get('name'),
                   'tags': sensor.get('tags'),
		   
                   'metadata': sensor.get('metadata'),
                   'source_identifier': sensor.get('source_identifier'),
                   'source_name': sensor.get('source_name')
                   }
    return json_object

def create_response(sensors):
    """Iterates over the list and generates a json response of sensors list
    Args as data:
        list of sensor retrieved from MongoDB
    Returns:
        {
            List of formatted sensor objects
        }
    """
    sensor_list = []
    for sensor in sensors:
        json_temp = create_json(sensor)
        sensor_list.append(json_temp)
    return sensor_list

def validate_users(emails,list_format=False):
    """Check if user exists"""
    for email in emails:
        if not list_format:
            if User.objects(email=email['user_id']).first() is None:
                return False
        else:
            if User.objects(email=email).first() is None:
                return False
    return True

def get_admins(name):
    """Get the list of admins in the DataService"""
    obj = DataService.objects(name=name).first()
    if obj is None:
        return []
    return list(obj.admins)

def add_delete_users(old, now):
    user_old,user_new = [],[]
    for user in old:
        user_old.append(user['user_id'])
    for user in now:
        user_new.append(user['user_id'])
    old, now = set(user_old), set(user_new)
    return now - old, old - now

def get_ds(sensor,building=None):
    args = {}
    args['buildings__all'] = [building if building else Sensor.objects(name=sensor).first().building]
    dataservices = DataService.objects(**args)
    return dataservices.first().name

def get_sg_ds(sensor_group):
    args = {}
    sg = SensorGroup.objects(name=sensor_group).first()
    args['buildings__all'] = [sg.building]
    dataservices = DataService.objects(**args)
    return dataservices.first().name

