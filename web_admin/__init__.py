# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
from flask_redis import FlaskRedis
from kael.work_frame import WORK_FRAME
from common import get_reg_blueprint
from monkey import patch_erro_handler
from flask import Flask

APP_NAME = "web_admin"
app = Flask(APP_NAME)
app.config.from_object('{0}.settings'.format(__name__))
WF = WORK_FRAME("test", app=app)
kael_client = lambda name: WORK_FRAME(name=name, app=app)
redis = FlaskRedis(app)
patch_erro_handler(app)

for bl in get_reg_blueprint(['tools', 'common']):
    app.register_blueprint(blueprint=bl)
