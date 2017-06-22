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


@blueprint.route("/<string:namespace>/status", versions=[1], stream=True)
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


@blueprint.route("/<namespace>/update/<pkg_type>/<service>", versions=[1])
def server_update(namespace, pkg_type, service):
    client = kael_client(namespace)
    res = client._update_pkg_client_helper(service, pkg_type)
    _restart_command(client, pkg_type, res)
    return res


@blueprint.route("/<namespace>/install/<pkg_type>/<service>/<path:install_path>", versions=[1])
def server_install(namespace, pkg_type, service, install_path):
    client = kael_client(namespace)
    res = client._install_pkg_client_helper(service, pkg_type, install_path)
    _restart_command(client, pkg_type, res)
    return res


def _restart_command(client, pkg_type, res_msg):
    if pkg_type == 'crontab':
        client.command('restart_crontab')
    elif pkg_type == 'service':
        for server, msg in res_msg:
            if msg.split('.')[0] == 'Update OK':
                client.command('restart_service', id=server)
