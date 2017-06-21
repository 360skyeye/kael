# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
from . import blueprint
from .. import WF
import time
import uuid


@blueprint.route("/hi/", methods=['GET'], versions=[1])
def hello():
    r = WF.get_last_version()
    return r


@blueprint.route("/stream/", versions=[1], stream=True)
def subscribe():
    while True:
        result = time.time()
        time.sleep(2)
        yield result


@blueprint.route("/pull/<string:topic>", versions=[1], stream=True)
def pull(topic):
    id = str(uuid.uuid4())
    WF.create_queue(id, exclusive=True, auto_delete=True, )
    while True:
        for i in WF.pull_msg(id, topic):
            yield i[-1]
        time.sleep(2)
