# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
from . import blueprint
from .. import WF, kael_client
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
        time.sleep(5)
        yield result


@blueprint.route("/pull/<string:topic>", versions=[1], stream=True)
def pull(topic):
    id = str(uuid.uuid4())
    WF.create_queue(id, exclusive=True, auto_delete=True, )
    while True:
        for i in WF.pull_msg(id, topic):
            yield i[-1]
        time.sleep(2)


@blueprint.route("/status/<string:namespace>", versions=[1], stream=True)
def server_status(namespace):
    client = kael_client(namespace)
    while True:
        time.sleep(2)
        r = client.command("get_pkg_version", pkg_type='service')
        data = client.get_response(r)
        yield dict(service=data)
        time.sleep(2)
        r = client.command("get_pkg_version", pkg_type='crontab')
        data = client.get_response(r)
        yield dict(crontab=data)

