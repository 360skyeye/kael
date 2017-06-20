# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
from flask import Blueprint

flag = "/{0}".format(__name__.replace("web_admin.", ""))
blueprint = Blueprint(__name__, __name__, url_prefix=flag)
