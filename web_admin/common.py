# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
from bson import ObjectId
from datetime import datetime, date
from flask import current_app, request, make_response
import simplejson as json
from web_admin import exceptions

import web_admin
import os
import pkgutil


def json_converter(f):
    """Converts `dict`, list or mongo cursor to JSON.
    Creates `~flask.Response` object and sets headers.
    """

    def decorator(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
        except Exception as e:
            raise e
        result = to_json({
            'status': exceptions.OK,
            'msg': None,
            'data': result
        })
        response = make_response(result)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.headers['Access-Control-Allow-Origin'] = '*'
        # response.headers['Access-Control-Allow-Headers'] = 'Accept, Content-Type, Skyeye-Token'
        # response.headers['Access-Control-Request-Method'] = 'OPTIONS, HEAD, GET'
        return response

    return decorator


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def to_json(content):
    """Converts content to json while respecting config options."""
    indent = None
    separators = (',', ':')

    if current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] and not request.is_xhr:
        indent = 2
        separators = (', ', ': ')
    return json.dumps(content, indent=indent, separators=separators, cls=JsonEncoder)


def get_reg_blueprint(extlist=[]):
    bls = []
    pkgpath = os.path.dirname(web_admin.__file__)
    for _, name, is_package in pkgutil.iter_modules([pkgpath]):
        if is_package and name not in extlist:
            try:
                module = __import__("web_admin.{0}.view".format(name), fromlist=["blueprint"])
                bl = module.blueprint
                bls.append(bl)
            except Exception, err:
                import traceback
                traceback.print_exc()
                print "URL MAP ERROR: [%s]" % err
                continue
    return bls
