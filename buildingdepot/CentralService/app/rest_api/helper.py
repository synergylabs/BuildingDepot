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