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
import smtplib
from . import responses


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

def send_registration_email(user_name,to_email,password):
    sender = current_app.config['ADMIN_ID']
    receivers = [to_email]

    message = responses.registration_email%(sender,user_name,to_email,to_email,password)

    try:
       smtpObj = smtplib.SMTP('localhost')
       smtpObj.sendmail(sender, receivers, message)
    except smtplib.SMTPException:
       print "Failed to send registration mail to %s"%(to_email)

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