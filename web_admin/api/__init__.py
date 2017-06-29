# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
from flask.config import Config
from .. import app, APP_NAME
from ..monkey import patch_flask_route, patch_validate_handler
from ..blueprint_factory import bl

blueprint = bl

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
