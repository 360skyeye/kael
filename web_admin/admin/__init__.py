# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
from flask import Blueprint
from web_admin import app
from flask.config import Config

flag = "/{0}".format(__name__.replace("web_admin.", ""))
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
