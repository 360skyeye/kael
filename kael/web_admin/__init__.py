# -*- coding: utf-8 -*-
from flask_redis import FlaskRedis
from kael.work_frame import WORK_FRAME
from common import get_reg_blueprint, RegexConverter
from monkey import patch_erro_handler, patch_url_convert
from flask import Flask

APP_NAME = "web_admin"
app = Flask(APP_NAME, instance_relative_config=True)
app.config.from_object('{0}.settings'.format(__name__))
app.config.from_pyfile('settings.py', silent=True)

kael_client = lambda name: WORK_FRAME(name=name, app=app)
redis = FlaskRedis(app)
patch_erro_handler(app)
patch_url_convert("regex", RegexConverter, app)

for bl in get_reg_blueprint(['tools', 'common']):
    app.register_blueprint(blueprint=bl)
