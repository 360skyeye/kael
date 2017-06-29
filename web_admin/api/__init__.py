# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
from flask import Blueprint
from .. import app, APP_NAME
from ..monkey import patch_flask_route, patch_validate_handler, patch_url_convert
from flask.config import Config
from ..common import RegexConverter

flag = "/{0}".format(__name__.replace("{0}.".format(APP_NAME), ""))
blueprint = Blueprint(__name__, __name__, url_prefix=flag)

try:
    c = Config("./")
    c.from_object("{0}.settings".format(__name__))
    confict = set(c.keys()) & set(app.config.keys())
    for k in confict:
        c.pop(k)
    app.config.update(c)
except:
    pass

patch_flask_route(blueprint, api=True, json=True)
patch_validate_handler(APP_NAME, blueprint)
patch_url_convert("regex", RegexConverter, app)
