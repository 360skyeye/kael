# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
import sys
from .forms import get_mapping
from kael.validate import formatchecker
from jsonschema import validate
from .exceptions import ArgumentError, BaseError, UnknownError
from flask import request
import simplejson as json
from common import json_converter, stream_gen

_view_map = {}


def patch_flask_route(bl=None, json=False, api=False):
    def _route(self, rule, **options):
        def decorator(f, rule=rule):
            raw_func = getattr(f, '__raw_func__', None) or f
            stream = options.pop('stream', None)
            endpoint = options.pop("endpoint", raw_func.__name__)
            versions = options.pop('versions', None)
            if not versions:
                versions = [1]

            if raw_func not in _view_map:
                if json:
                    if not stream:
                        f = json_converter(f)
                if stream:
                    f = stream_gen(f, json)
                f.__raw_func__ = raw_func
                _view_map[raw_func] = f
            else:
                f = _view_map[raw_func]

            if api:
                for v in versions:
                    v_rule = '/v%d%s' % (v, rule)
                    self.add_url_rule(v_rule, endpoint, f, **options)
            else:
                self.add_url_rule(rule, endpoint, f, **options)
            return f

        return decorator

    if bl:
        bl.__class__.route = _route
    else:
        sys.modules['flask'].Flask.route = _route
        sys.modules['flask'].Blueprint.route = _route


def patch_validate_handler(name, bl=None):
    def params_validate_handler():
        if not request.endpoint \
                or not request.endpoint.startswith('{0}.'.format(name)) \
                or request.method == 'HEAD':
            return
        _, blueprint, endpoint = request.endpoint.split('.')
        mapping = get_mapping(blueprint, endpoint)
        if mapping:
            params = request.get_json()
            if validate(params, mapping, format_checker=formatchecker):
                raise ArgumentError('Json schema validate failed')

    if bl:
        bl.before_app_first_request(params_validate_handler)
    else:
        sys.modules['flask'].app.before_app_first_request(params_validate_handler)

    return params_validate_handler


def patch_erro_handler(bl=None):
    def common_error_handler(exc):
        import traceback
        traceback.print_exc()
        if not isinstance(exc, BaseError):
            exc = UnknownError(str(exc))
        return json.dumps({
            'status': exc.status,
            'msg': exc.description,
            'data': None
        })

    if bl:
        bl._register_error_handler(None, Exception, common_error_handler)
    else:
        sys.modules['flask'].app._register_error_handler(None, Exception, common_error_handler)


def patch_url_convert(convert, converter, app):
    app.url_map.converters[convert] = converter
