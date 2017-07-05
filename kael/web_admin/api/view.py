# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
from flask import request

from . import blueprint
from .. import kael_client
import time
import uuid


@blueprint.route("/<string:namespace>/hi/", methods=['GET'], versions=[1])
def hello(namespace):
    client = kael_client(namespace)
    return client.get_last_version()


@blueprint.route("/stream/", versions=[1], stream=True)
def subscribe(uid):
    while True:
        result = time.time()
        time.sleep(2)
        yield result


@blueprint.route("/<string:namespace>/pull/<string:topic>", versions=[1], stream=True)
def pull(namespace, topic):
    uid = str(uuid.uuid4())
    client = kael_client(namespace)
    client.create_queue(uid, exclusive=True, auto_delete=True, )
    while True:
        for i in client.pull_msg(uid, topic):
            yield i[-1]
        time.sleep(2)


@blueprint.route("/<string:namespace>/status", versions=[1], stream=True)
def server_status(namespace):
    client = kael_client(namespace)
    while True:
        time.sleep(1)
        data = client.package_status(pkg_type='service')
        yield dict(service=data)
        time.sleep(1)
        data = client.package_status(pkg_type='crontab')
        yield dict(crontab=data)


@blueprint.route("/<string:namespace>/rpc/<string:fun_name>", methods=['GET', 'POST'], versions=[1])
def server_rpc(namespace, fun_name):
    """
    RPC, 微服务调用。POST方法接收参数, 1函数名:func 2args: [] 3kwargs: {}
    :param namespace: 运行空间
    :param fun_name: 运行函数名
    :return: GET:返回函数参数格式  POST:返回微服务调用返回值
    """
    client = kael_client(namespace)
    if request.method == 'GET':
        service_name, func = fun_name.strip().split('__')
        return client.get_last_version(service=service_name).get(service_name, {}).get('args', {}).get(func)
    arguments = request.get_json()
    args = arguments.get('args', [])
    kwargs = arguments.get('kwargs', {})

    if not fun_name:
        raise NameError('No function name')

    return getattr(client, fun_name)(*args, **kwargs)


@blueprint.route("/<namespace>/operation", methods=['POST'], versions=[1])
def server_update_install(namespace):
    """update/install/restart，全参数POST"""
    kwargs = request.get_json()
    # 必选
    operation = kwargs.get('operation')  # install update restart
    pkg_type = kwargs.get('pkg_type')  # service crontab
    package = kwargs.get('package')
    install_path = kwargs.get('install_path')
    # 可选
    version = kwargs.get('version')
    server_id = kwargs.get('server_id')  # 只向某机器发送
    server_not_id = kwargs.get('server_not_id')  # 不向一些机器发送

    if operation not in ('update', 'install', 'restart'):
        return 'No operation %s' % operation

    if pkg_type not in ('crontab', 'service'):
        return 'No pkg_type %s' % pkg_type

    client = kael_client(namespace)
    if operation == 'restart':
        return client.restart_servers(pkg_type, id=server_id, not_id=server_not_id)

    if not package:
        return 'No package'

    if operation == 'install':
        if not install_path:
            return 'No install_path'
        res = client._install_pkg_client_helper(package, pkg_type, install_path,
                                                version=version, id=server_id, not_id=server_not_id)

    else:
        res = client._update_pkg_client_helper(package, pkg_type, version=version, id=server_id, not_id=server_not_id)

    client.restart_servers(pkg_type, id=server_id)
    return res
