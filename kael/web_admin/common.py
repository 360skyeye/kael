# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
import os
import pkgutil
import types
from datetime import date, datetime
# import web_admin
import simplejson as json
from bson import ObjectId
from flask import Response, current_app, make_response, request, stream_with_context
from werkzeug.routing import BaseConverter

from kael.web_admin import exceptions


class ListConverter(BaseConverter):
    def to_python(self, value):
        return value.split(',')

    def to_url(self, values):
        return ','.join(BaseConverter.to_url(value)
                        for value in values)


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


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
    try:
        if current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] and not request.is_xhr:
            indent = 2
            separators = (', ', ': ')
    except:
        pass
    return json.dumps(content, indent=indent, separators=separators, cls=JsonEncoder)


def get_reg_blueprint(extlist=None):
    if not extlist:
        extlist = []
    bls = []
    # pkgpath = os.path.dirname(web_admin.__file__)
    pkgpath = os.path.dirname(os.path.realpath(__file__))
    for _, name, is_package in pkgutil.iter_modules([pkgpath]):
        if is_package and name not in extlist:
            try:
                module = __import__("kael.web_admin.{0}.view".format(name), fromlist=["blueprint"])
                bl = module.blueprint
                bls.append(bl)
            except Exception, err:
                import traceback
                traceback.print_exc()
                print "URL MAP ERROR: [%s]" % err
                continue
    return bls


class ServerSentEvent(object):
    def __init__(self, data):
        self.data = data
        self.event = None
        self.id = None
        self.desc_map = {
            self.data: "data",
            self.event: "event",
            self.id: "id"
        }

    def encode(self):
        if not self.data:
            return ""
        lines = ["%s: %s" % (v, k)
                 for k, v in self.desc_map.iteritems() if k]

        return "%s\n\n" % "\n".join(lines)


def stream_gen(f, flag=False):
    def decorator(*args, **kwargs):
        def SEE(ctx):
            for i in ctx:
                if flag:
                    data = to_json(
                        {
                            'status': exceptions.OK,
                            'msg': None,
                            'data': i,
                        }
                    )
                else:
                    data = str(i)
                ev = ServerSentEvent(data)
                yield ev.encode()

        rf = f(*args, **kwargs)
        if isinstance(rf, types.GeneratorType):
            return Response(stream_with_context(SEE(rf)), mimetype="text/event-stream")
        else:
            raise exceptions.InternalError

    return decorator
