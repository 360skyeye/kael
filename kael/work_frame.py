#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
import inspect
import logging
import os
import random
import time
import uuid
import zipfile
from io import BytesIO
from functools import wraps

import gevent.monkey
from gevent.pool import Pool

from microservice import micro_server
from service_manage import get_service_group, update_service_group

gevent.monkey.patch_all()
DEFAULT_TIMEOUT = 1


def Command(func):
    @wraps(func)
    def warp(cls, *args, **kwargs):
        return func(cls, *args, **kwargs)

    return warp


class WORK_FRAME(micro_server):
    command_fun = {}

    def __init__(self, name=None, service_group_conf=None, app=None, channel="center", lock=False, auri=None):
        # 指定name最优先，service_group_conf中的service_group次之
        if not name:
            if service_group_conf:
                name = get_service_group(service_group_conf).get('service_group')
            if not name:
                raise EnvironmentError('Neither name given nor service_group_conf name given')
        super(WORK_FRAME, self).__init__(name, app=app, channel=channel, auri=auri, lock=lock)
        self.command_q = "{0}-{1}".format(self.name, self.id)
        # frame停止运行,没有任何consumer消费20s后自动删除command_q
        self.create_queue(self.command_q, ttl=15, args={'x-expires': 20000})
        self.command_prefix = "skyeye-rpc-{0}.".format(self.name)
        self.join(self.command_q, "{0}*".format(self.command_prefix))
        self.init_command()
        self.command_pool = Pool(100)
        self.service_group_conf = service_group_conf

    def init_service(self):
        """
            frame_start时调用, 载入service包到self.loaded_services
            最后self.loaded_services结构：
            {
                'calculate': {
                    'path': '/data/project/mq-service/services_default/sleep_service',
                    'version': 1.0,
                    'services': {
                        'calculate__add': <function add at 0x00000000029C7AC8>,
                        'calculate__minus': <function minus at 0x00000000029C7B38>
                    }
                },
                'time': {
                    'path': '/data/project/mq-service/services_default/time_service',
                    'version': 1.0,
                    'services': {
                        'time__transfer': <function transfer at 0x00000000029C7F28>
                    }
                }
            }
        """
        if not self.service_group_conf:
            raise ImportError('No Config of Service Group: service_group_conf')
        self.loaded_services = get_service_group(self.service_group_conf).get('service_pkg', {})
        for service_pkg, value in self.loaded_services.iteritems():
            for service_name, func in value['services'].iteritems():
                self.services.update({service_name: func})

    def init_crontabs(self):
        """
        frame_start时调用, 调用rpc检查是否已有相同名称的定时任务启动
        1 检查其他机器所有cron状态
        2 对比自身载入的所有crontab。
        3 存在则设置状态False； 不存在则设置状态True ,并设置微服务层定时任务

        最后self.loaded_crontab的结构：
        {
            'print':{
                'path':'/data/project/mq-service/services_default/task1_crontab',
                'version': 1.0,
                'crontabs':[ {'time_str': '', 'command': ''}, {} ]
                'status': True
            }
            'sql':{
                'path':'/data/project/mq-service/services_default/sql_crontab',
                'version': 1.1,
                'crontabs':[ {'time_str': '', 'command': ''}, {} ]
                'status': False
            }
        }
        """
        self.loaded_crontab = get_service_group(self.service_group_conf).get('crontab_pkg', {})
        # 这里有RPC调用等待操作
        all_servers_crontab_status = self.get_all_crontab_status()
        for crontab_pkg, value in self.loaded_crontab.iteritems():
            need_cron_start = True
            for server, cron_dicts in all_servers_crontab_status.iteritems():
                if cron_dicts.get(crontab_pkg, {}).get('status'):
                    need_cron_start = False
                    break

            # 所有服务器上没有已启动的<crontab_pkg>
            if need_cron_start:
                # 设置定时任务，定时任务可能设置不成功，此时也应该置为False
                if self.set_crontabs(cron_name=crontab_pkg, jobs=value['crontabs']):
                    value['status'] = True
                else:
                    value['status'] = False
            else:
                value['status'] = False

    def frame_start(self, process_num=2, daemon=True):
        """框架启动"""
        s = """                                               :      .-.
                      7                         M-   Z.7 O$..-
               ;7.    : ;-!; > -W>.      ;7.?>   $H  H-Q> 7O
                7    .AQ ??; O:>     ?? ;?  H $   7M?Uz ?>.
                  .-H---! ?? .TQ    ; ?.>!? -C!:!; E.O. $$
                     Q    :  !>:360SKYEYE-!  7   ;> $ C!;M:.
                       .>.;!   :    !.O   H  M 7!! ;C .
                        W;.A    -T E    . R >.7> >>.O
                           ;N-      C;!>M; :> H-
          .MMMMM       HMMM               $                     .?
             M       .Q                                          M
             H      MM                                           M
             H    !M                                             M
             H   H;              MHOCC$HM MMM      ?MHHMM.       M
             N MMMN$           7M        MH      MM       M>     M
             NN     MO        !M          H     N        CQ7     M
             H       7M       M.          H    :M     C$?        M
             H        :M      M           H    !!  MM .          M
             H         MN     !M          H     NM-      MM      M
             H          MC     MM        QN      Q        CMM    M
          !MMMMN         :N      MM7..7MM MNMH    -MM77MHM     QNMNN:"""
        print s
        print 80 * '-'
        print 'WORK FRAME START'
        print self.command_q, '\n', 80 * '-'

        self.init_service()
        self.start_service(process_num, daemon=daemon)

        self.init_crontabs()
        self.start_crontab()

        channel = self.connection.channel()
        channel.basic_consume(self.process_command,
                              queue=self.command_q, no_ack=False)
        try:
            channel.start_consuming()
        except Exception:
            self.connection = self.connect()
            channel = self.connection.channel()
            channel.start_consuming()

    def process_command(self, ch, method, props, body):
        """server中的命令执行函数"""

        def run(*args, **kwargs):
            try:
                result = fn(*args, **kwargs)
            except Exception as e:
                result = "ERR command {}: {}".format(fn.__name__, e.message)
            rbody = result
            self.push_msg(qid=self.command_q, topic="", msg=rbody, reply_id=props.correlation_id, session=ch,
                          to=props.reply_to)

        ch.basic_ack(delivery_tag=method.delivery_tag)
        body = self.decode_body(body)
        args, kwargs = body
        rtk = method.routing_key.replace(self.command_prefix, "")
        # 有not_id指定  '!@'
        not_server_ids = rtk.split('!@')[1:]
        if self.command_q in not_server_ids:
            return

        # 有id指定
        rtk = rtk.split('!@')[0]  # remove not_id
        buf = rtk.split("@")
        rtk = buf[0]
        if len(buf) > 1:
            server_id = buf[1]
            if self.command_q != server_id:
                return

        fn = self.command_fun.get(rtk)
        if fn:
            if fn == self._restart_service:
                run(*args, **kwargs)
            else:
                self.command_pool.spawn(run, *args, **kwargs)

    def command(self, name=None, *args, **kwargs):
        """work frame客户端命令调用函数"""
        # 指定发送机器
        id = kwargs.pop("id", None)
        # 指定不发送机器
        not_id = kwargs.pop("not_id", [])
        if name and name in self.command_fun:
            if id:
                topic = "{0}{1}@{2}".format(self.command_prefix, name, id)
            else:
                if not_id:
                    not_string = '!@'.join(not_id) if isinstance(not_id, list) else not_id
                    topic = "{0}{1}!@{2}".format(self.command_prefix, name, not_string)
                else:
                    topic = "{0}{1}".format(self.command_prefix, name)
            qid = "command_{0}.{1}.{2}".format(self.command_q, name, uuid.uuid4())
            self.create_queue(qid, exclusive=True, auto_delete=True, )
            self.push_msg(qid, topic=topic, msg=(args, kwargs), ttl=15)
            return qid

    def get_response(self, qid, timeout=0):
        """work frame 客户端结果获取函数"""
        if timeout:
            # time.sleep(timeout)
            # self.connection.process_data_events(time_limit=timeout)
            self.connection.sleep(timeout)
        try:
            ch = self.connection.channel()
        except:
            self.connection = self.connect()
            ch = self.connection.channel()
        ctx = self.pull_msg(qid=qid, session=ch)
        return {i[1].reply_to: i[-1] for i in ctx}

    @classmethod
    def methodsWithDecorator(cls, decoratorName):
        sourcelines = inspect.getsourcelines(cls)[0]
        for i, line in enumerate(sourcelines):
            line = line.strip()
            if line.split('(')[0].strip() == '@' + decoratorName:  # leaving a bit out
                nextLine = sourcelines[i + 1]
                name = nextLine.split('def')[1].split('(')[0].strip()
                yield (name)

    def init_command(self):
        l = self.methodsWithDecorator("Command")
        for func in l:
            fun = getattr(self, func)
            self.command_fun.setdefault(func, fun)

    # region RPC COMMAND FUNCTION
    @Command
    def system(self, cmd):
        output = os.popen(cmd)
        data = output.read()
        output.close()
        return data

    @Command
    def _restart_service(self, process_num=2, daemon=True, **kwargs):
        self.stop_service()
        # queue will auto delete, need recreate
        time.sleep(1)
        self.init_service()
        self.start_service(n=process_num, daemon=daemon)
        return 'restart service ok'

    @Command
    def _restart_crontab(self, **kwargs):
        self.stop_crontab()
        self.loaded_crontab.clear()
        # random restart in case all set
        time.sleep(random.choice([0.01, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5]))
        self.init_crontabs()
        self.start_crontab()
        return 'restart crontab ok'

    @Command
    def _get_pkg_version(self, pkg=None, pkg_type='service'):
        """获取service或crontab包的版本"""
        rdata = {}
        if pkg_type == 'service':
            loaded_pkg = self.loaded_services
            pop_item = 'services'
        elif pkg_type == 'crontab':
            loaded_pkg = self.loaded_crontab
            pop_item = 'crontabs'
        else:
            return {}

        if not pkg:
            for i in loaded_pkg:
                data = copy.deepcopy(loaded_pkg[i])
                data.pop(pop_item)
                rdata.setdefault(i, data)
        else:
            if pkg not in loaded_pkg:
                rdata = {}
            else:
                data = copy.deepcopy(loaded_pkg[pkg])
                data.pop(pop_item)
                rdata = {pkg: data}

        return rdata

    @Command
    def _get_crontab_status(self, crontab=None):
        if crontab:
            content = self.loaded_crontab.get(crontab)
            return {crontab: content} if content else {}
        return self.loaded_crontab

    @Command
    def _zip_pkg(self, pkg, pkg_type):
        if pkg_type == 'service':
            pkg_path = self.loaded_services[pkg]['path']
        elif pkg_type == 'crontab':
            pkg_path = self.loaded_crontab[pkg]['path']
        else:
            return
        tmp = BytesIO()
        cwd = os.getcwd()
        os.chdir(pkg_path)
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk('.'):
                for f in files:
                    if f.split('.')[-1] != 'pyc':
                        z.write(os.path.join(root, f), compress_type=zipfile.ZIP_DEFLATED)

        res = tmp.getvalue()
        tmp.close()
        os.chdir(cwd)
        return res

    @Command
    def _update_pkg(self, fid_version, pkg, pkg_type, timeout=DEFAULT_TIMEOUT):
        return self._update_and_install_pkg(fid_version, pkg, pkg_type=pkg_type, timeout=timeout)

    @Command
    def _install_pkg(self, fid_version, pkg, pkg_type, install_path, timeout=DEFAULT_TIMEOUT):
        if pkg_type == 'service':
            loaded_pkg = self.loaded_services
        elif pkg_type == 'crontab':
            loaded_pkg = self.loaded_crontab
        else:
            return 'ERR: package must be service or crontab'

        # check whether service is installed
        if pkg in loaded_pkg:
            if fid_version['version'] == loaded_pkg.get(pkg, {}).get('version'):
                return 'Package <{}> Version <{}> Already on this server'.format(pkg, fid_version['version'])
            else:
                return 'Package <{}> Version <{}> Already on this server. Please use update command to version <{}>'. \
                    format(pkg, loaded_pkg.get(pkg, {}).get('version'),
                           fid_version['version'])

        # install_path为相对路径时，更改为绝对路径
        if not os.path.isabs(install_path) and type(self.service_group_conf) in (str, unicode):
            service_group_dir = os.path.dirname(os.path.realpath(self.service_group_conf))
            install_path = os.path.realpath(os.path.join(service_group_dir, install_path))
        if not os.path.exists(install_path):
            try:
                os.makedirs(install_path)
            except Exception as e:
                if not os.path.exists(install_path):
                    logging.exception(e)
                    return 'ERR: install fail, cannot make dir {}. {}'.format(install_path, e.message)

        res = self._update_and_install_pkg(fid_version, pkg,
                                           pkg_type=pkg_type,
                                           install_path=install_path,
                                           timeout=timeout)
        if res.split('.')[0] != 'Update OK':
            return res
        # install service: 需将service group载入的文件更新(只针对配置文件启动)
        update_service_group(self.service_group_conf, install_path)
        return "{}, {}".format(res, install_path)

    def _update_and_install_pkg(self, fid_version, pkg, pkg_type, install_path=None, timeout=DEFAULT_TIMEOUT):
        """
        被更新服务端发起, 更新服务不需要install_path， 安装服务需要install_path
        update service -->  install_path=None, use existed path
        install service --> install_path is not None, use install_path

        :param fid_version: source code provider server id & code version
        :param pkg: the service name which needed update or install
        :param pkg_type: service or crontab
        :param install_path: if service not exist in server, need install_path to deploy
        :param timeout:
        :return: execution message
        """
        if pkg_type == 'service':
            loaded_pkg = self.loaded_services
        elif pkg_type == 'crontab':
            loaded_pkg = self.loaded_crontab
        else:
            return 'ERR: package must be service or crontab'

        from_server_id, from_server_version = fid_version['fid'], fid_version['version']
        old_version = loaded_pkg.get(pkg, {}).get('version')
        if from_server_id == self.command_q:
            return 'I am the source code'

        if from_server_version == old_version:
            return 'Package <{}> Version <{}> Already on the server'.format(pkg, from_server_version)

        r = self.command('_zip_pkg', pkg, pkg_type, id=from_server_id)
        data = self.get_response(r, timeout=timeout)
        if not data:
            return 'ERR: No Zip Content from get_response'

        content = data[from_server_id]
        if not content:
            return 'ERR: No Zip Content. From {}, To {}'.format(from_server_id, self.command_q)

        # update service -->  install_path=None, use existed path
        # install service --> install_path is not None, use install_path
        self_server_path = loaded_pkg.get(pkg, {}).get('path')
        if not self_server_path and not install_path:
            return 'ERR: No Package AND No install_path. Cannot update or install on {}:'.format(self.command_q)

        if install_path:
            self_server_path = install_path

        cwd = os.getcwd()
        os.chdir(self_server_path)
        with BytesIO() as tmp:
            tmp.write(content)
            with zipfile.ZipFile(tmp, 'r', zipfile.ZIP_DEFLATED) as z:
                try:
                    z.extractall()
                except Exception as e:
                    logging.exception(e)
                    return 'ERR: extract failed, {}'.format(e.message)
        os.chdir(cwd)
        return 'Update OK. Version from <{}> to <{}>'.format(old_version, from_server_version)

    # endregion

    # region client operation function

    def package_status(self, **kwargs):
        timeout = kwargs.pop('timeout', DEFAULT_TIMEOUT)
        r = self.command("_get_pkg_version", **kwargs)
        return self.get_response(r, timeout=timeout)

    def get_last_version(self, service=None, pkg_type='service', timeout=DEFAULT_TIMEOUT):
        """获取service或crontab的最新版本"""
        data = self.package_status(pkg=service, pkg_type=pkg_type, timeout=timeout)
        last_dict = {}
        for id in data:
            for service in data[id]:
                tmp = {
                    'version': data[id][service]["version"],
                    'path': data[id][service]["path"],
                    'id': id,
                }
                if pkg_type == 'service':
                    tmp.update({'args': data[id][service]["args"] or {}})

                t = last_dict.get(service)
                if t and data[id][service]["version"] > t.get('version'):
                    last_dict[service] = tmp
                else:
                    last_dict.setdefault(service, tmp)
        return last_dict

    def get_all_crontab_status(self, crontab=None):
        """获取所有crontab状态"""
        r = self.command('_get_crontab_status', crontab)
        return self.get_response(r)

    def restart_servers(self, pkg_type, **kwargs):
        """
        client: 重启
        :param pkg_type: service or crontab
        :param kwargs:
        :return: data
        """
        timeout = kwargs.pop('timeout', DEFAULT_TIMEOUT)
        if pkg_type == 'service':
            r = self.command('_restart_service', **kwargs)
        elif pkg_type == 'crontab':
            r = self.command('_restart_crontab', **kwargs)
        else:
            return 'ERR: pkg_type must be service or crontab'
        return self.get_response(r, timeout=timeout)

    def update_service(self, service_pkg, version=None, id=None, not_id=None, timeout=DEFAULT_TIMEOUT):
        """客户端：更新服务"""
        return self._update_pkg_client_helper(service_pkg, 'service', version, id, not_id, timeout)

    def update_crontab(self, crontab_pkg, version=None, id=None, not_id=None, timeout=DEFAULT_TIMEOUT):
        """客户端：更新定时任务"""
        return self._update_pkg_client_helper(crontab_pkg, 'crontab', version, id, not_id, timeout)

    def install_service(self, service_pkg, service_install_path, version=None, id=None, not_id=None,
                        timeout=DEFAULT_TIMEOUT):
        """客户端：安装服务"""
        return self._install_pkg_client_helper(service_pkg, 'service', service_install_path,
                                               version, id, not_id, timeout)

    def install_crontab(self, crontab_pkg, service_install_path, version=None, id=None, not_id=None,
                        timeout=DEFAULT_TIMEOUT):
        """客户端：安装定时任务"""
        return self._install_pkg_client_helper(crontab_pkg, 'crontab', service_install_path,
                                               version, id, not_id, timeout)

    # endregion
    def _update_pkg_client_helper(self, pkg, pkg_type, version=None, id=None, not_id=None, timeout=DEFAULT_TIMEOUT):
        print '--- Update {} <{}> to Version <{}> ---'.format(pkg_type, pkg, version if version else 'latest')
        fid_version = self._get_source_service_server_id(pkg, pkg_type=pkg_type, version=version, timeout=timeout)
        if fid_version:
            print '--- From Source server <{}> Version <{}> ---'.format(fid_version['fid'], fid_version['version'])
            r = self.command("_update_pkg", fid_version, pkg, pkg_type=pkg_type, id=id, not_id=not_id, timeout=timeout)
            data = self.get_response(r, timeout=timeout)
            data.update(self.get_response(r, timeout=timeout))
            return data
        print '--- No Source Server and Version Found ---'

    def _install_pkg_client_helper(self, pkg, pkg_type, service_install_path, version=None, id=None, not_id=None,
                                   timeout=DEFAULT_TIMEOUT):
        print '--- Update {} <{}> to Version <{}> ---'.format(pkg_type, pkg, version if version else 'latest')
        fid_version = self._get_source_service_server_id(pkg, pkg_type=pkg_type, version=version, timeout=timeout)
        if fid_version:
            print '--- From Source server <{}> Version <{}> ---'.format(fid_version['fid'], fid_version['version'])
            r = self.command("_install_pkg", fid_version, pkg, pkg_type=pkg_type, install_path=service_install_path,
                             id=id, not_id=not_id, timeout=timeout)
            data = self.get_response(r, timeout=timeout)
            data.update(self.get_response(r, timeout=timeout))
            return data
        print '--- No Source Server and Version Found ---'

    # 上层控制函数
    def _get_source_service_server_id(self, service_pkg, pkg_type='service', version=None, timeout=DEFAULT_TIMEOUT):
        fid_version = {}
        if not version:
            v = self.get_last_version(service_pkg, pkg_type=pkg_type).get(service_pkg)
            if v:
                fid_version = {'version': v.get('version'), 'fid': v.get('id')}
        else:
            r = self.command("_get_pkg_version", pkg=service_pkg, pkg_type=pkg_type)
            data = self.get_response(r, timeout=timeout, )
            for server_id, service in data.iteritems():
                if service_pkg not in service:
                    break
                if version == service[service_pkg]["version"]:
                    fid_version = {'version': version, 'fid': server_id}
                    break
        return fid_version


def main():
    pass


if __name__ == '__main__':
    main()
