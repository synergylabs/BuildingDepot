from functools import wraps

from flask import g, jsonify
from app.common import PAGE_SIZE
from ..errors import not_allowed
from flask.ext.restful import marshal, reqparse


def is_super(user):
    return user.role.type == 'super'


def is_local(user):
    return user.role.type == 'local'


def is_default(user):
    return user.role.type == 'default'


def is_managed_by_local(local_admin, user):
    if local_admin.buildings and user.buildings:
        return True
    return False


def super_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_super(g.user):
            return not_allowed('Only super admin is allowed for this method')
        return f(*args, **kwargs)
    return decorated_function


def success():
    response = jsonify({'success': 'True'})
    response.status_code = 200
    return response


def page_validator(page_num):
    try:
        page_num = int(page_num)
        if page_num <= 0:
            raise ValueError('Please input positive integer number for page number')
    except:
        raise ValueError('Please input integer number for page number')
    return page_num


def pagination_get(document_class, res_fields, api_class):
    parser = reqparse.RequestParser()
    parser.add_argument('page', type=page_validator, default=1, location='args')

    page = parser.parse_args()['page']
    skip_size = (page-1) * PAGE_SIZE
    objs = document_class.objects().skip(skip_size).limit(PAGE_SIZE)

    from ... import api
    res = {'data': [marshal(obj, res_fields) for obj in objs]}
    if page > 1:
        res['prev'] = api.url_for(api_class, _external=True, page=page-1)
    if len(res['data']) == PAGE_SIZE:
        res['next'] = api.url_for(api_class, _external=True, page=page+1)
    return res
