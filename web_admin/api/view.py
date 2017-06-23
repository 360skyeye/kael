# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
from flask import request

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


@blueprint.route("/<namespace>/operation", methods=['POST'], versions=[1])
def server_update_install(namespace):
    """更新安装功能，全参数POST"""
    kwargs = request.get_json()
    # 必选
    operation = kwargs.get('operation')  # install update
    pkg_type = kwargs.get('pkg_type')  # service crontab
    package = kwargs.get('package')
    install_path = kwargs.get('install_path')
    # 可选
    version = kwargs.get('version')
    server_id = kwargs.get('server_id')  # 只向某机器发送
    server_not_id = kwargs.get('server_not_id')  # 不向一些机器发送

    if pkg_type not in ('crontab', 'service'):
        return 'No pkg_type %s' % pkg_type
    if operation not in ('update', 'install'):
        return 'No operation %s' % operation
    if not package:
        return 'No package'

    if operation == 'install':
        if not install_path:
            return 'No install_path'
        client = kael_client(namespace)
        res = client._install_pkg_client_helper(package, pkg_type, install_path,
                                                version=version, id=server_id, not_id=server_not_id)
        _restart_command(client, pkg_type, res)

    else:
        client = kael_client(namespace)
        res = client._update_pkg_client_helper(package, pkg_type, version=version, id=server_id, not_id=server_not_id)
        _restart_command(client, pkg_type, res)
    return res


@blueprint.route("/<namespace>/update/<pkg_type>/<package>", versions=[1])
def server_update(namespace, pkg_type, package):
    client = kael_client(namespace)
    res = client._update_pkg_client_helper(package, pkg_type)
    _restart_command(client, pkg_type, res)
    return res


@blueprint.route("/<namespace>/install/<pkg_type>/<package>/<path:install_path>", versions=[1])
def server_install(namespace, pkg_type, package, install_path):
    client = kael_client(namespace)
    res = client._install_pkg_client_helper(package, pkg_type, install_path)
    _restart_command(client, pkg_type, res)
    return res


def _restart_command(client, pkg_type, res_msg):
    if pkg_type == 'crontab':
        client.command('restart_crontab')
    elif pkg_type == 'service':
        if res_msg:
            for server, msg in res_msg.iteritems():
                if msg.split('.')[0] == 'Update OK':
                    client.command('restart_service', id=server)
