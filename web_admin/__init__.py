# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
import os
import pkgutil
from flask import Flask, Response, current_app, request, json, jsonify
from flask_redis import FlaskRedis
import web_admin
from web_admin import exceptions
from kael import MQ
from web_admin.exceptions import BaseError, ArgumentError, UnknownError
from web_admin.forms import get_mapping
from kael.validate import formatchecker
from jsonschema import validate


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


def to_json(content):
    """Converts content to json while respecting config options."""
    indent = None
    separators = (',', ':')

    if current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] and not request.is_xhr:
        indent = 2
        separators = (', ', ': ')

    return (json.dumps(content, indent=indent, separators=separators), '\n')


class ResponseJSON(Response):
    """Extend flask.Response with support for list/dict conversion to JSON."""

    def __init__(self, content=None, *args, **kargs):
        if isinstance(content, (list, dict, str, int, float)):
            kargs['mimetype'] = 'application/json'
            content = to_json({
                'status': exceptions.OK,
                'msg': None,
                'data': content
            })

        super(Response, self).__init__(content, *args, **kargs)

    @classmethod
    def force_type(cls, response, environ=None):
        """Override with support for list/dict."""
        if isinstance(response, (list, dict)):
            return cls(response)
        else:
            return super(Response, cls).force_type(response, environ)


class FlaskJSON(Flask):
    """Extension of standard Flask app with custom response class."""
    response_class = ResponseJSON


app = FlaskJSON(__name__)
app.config.from_object('web_admin.settings')
mq = MQ(app)
redis = FlaskRedis(app)


@app.before_request
def params_validate_handler():
    if not request.endpoint \
            or not request.endpoint.startswith('webapi.') \
            or request.method == 'HEAD':
        return
    _, blueprint, endpoint = request.endpoint.split('.')
    mapping = get_mapping(blueprint, endpoint)
    if mapping:
        params = request.get_json()
        if validate(params, mapping, format_checker=formatchecker):
            raise ArgumentError('Json schema validate failed')


@app.errorhandler(Exception)
def common_error_handler(exc):
    import traceback
    traceback.print_exc()
    if not isinstance(exc, BaseError):
        exc = UnknownError(str(exc))
    return jsonify({
        'status': exc.status,
        'msg': exc.description,
        'data': None
    })


for bl in get_reg_blueprint(['tools', 'common']):
    app.register_blueprint(blueprint=bl)
