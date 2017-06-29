# -*- coding: utf-8 -*-
"""
https://stackoverflow.com/questions/2447353/getattr-on-a-module
"""
import sys
import inspect
from flask import Blueprint

bl = None


class Wrapper(object):
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __getattr__(self, key):
        if key == 'bl':
            AutoBlueprint = self.wrapped.AutoBlueprint
            return AutoBlueprint()
        return getattr(self.wrapped, key)


class AutoBlueprint(object):
    def __init__(self):
        frm = sys._getframe(2)
        mod = inspect.getmodule(frm)
        pack_name = mod.__name__.rsplit('.', 1)[-1]
        self._api = False
        self._json = False
        self.bl = Blueprint(mod.__name__, pack_name, url_prefix='/{0}'.format(pack_name))

    #
    # def _get_api(self):
    #     return self._api
    #
    # def _set_api(self, api):
    #     if self._api:
    #         raise RuntimeError
    #     if api:
    #         self._api = True
    #         self.bl.route = _route
    #
    # api = property(_get_api, _set_api)
    #
    # def _get_json(self):
    #     return self._json
    #
    # def _set_json(self, json):
    #     if self._json:
    #         raise RuntimeError
    #     if json:
    #         self._json = True
    #         self.bl.before_app_first_request()
    #
    # json = property(_get_json, _set_json)
    #
    # def configure(self, **kwargs):
    #     if 'api' in kwargs:
    #         self.api = kwargs['api']
    #     if 'json' in kwargs:
    #         self.json = kwargs['json']

    def __getattr__(self, key):
        return getattr(self.bl, key)


sys.modules[__name__] = Wrapper(sys.modules[__name__])
