# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
from .. import app
from ..blueprint_factory import bl
from flask.config import Config

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
