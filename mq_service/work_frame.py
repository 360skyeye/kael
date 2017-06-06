# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/5/20

import copy
import inspect
import os
import time
import uuid
import zipfile
from io import BytesIO

import gevent.monkey
from gevent.pool import Pool

from microservice import micro_server
from mq_service.service_manage import get_service_group

gevent.monkey.patch_all()


def Command(func):
    def warp(cls, *args, **kwargs):
        return func(cls, *args, **kwargs)

    return warp


class WORK_FRAME(micro_server):
    command_fun = {}

    def __init__(self, name, service_group_conf=None, app=None, channel="center", lock=False, auri=None):
        super(WORK_FRAME, self).__init__(name, app=app, channel=channel, auri=auri, lock=lock)
        self.command_q = "{0}-{1}".format(self.name, self.id)
        self.create_queue(self.command_q, ttl=15)
        self.command_prefix = "skyeye-rpc-{0}.".format(self.name)
        self.join(self.command_q, "{0}*".format(self.command_prefix))
        self.init_command()
        self.command_pool = Pool(100)
        self.service_group_conf = service_group_conf

    def init_service(self):
        if not self.service_group_conf:
            raise ImportError('No Config of Service Group: service_group_conf')
        self.loaded_services = get_service_group(self.service_group_conf)
        for service_pkg, value in self.loaded_services['service_pkg'].iteritems():
            for service_name, func in value['services'].iteritems():
                self.services.setdefault(service_name, func)

    def frame_start(self, process_num=2, daemon=True):
        """框架启动"""
        print 'WORK FRAME START'
        print self.command_q
        self.init_service()
        self.start(process_num, daemon=daemon)
        channel = self.connection.channel()
        channel.basic_consume(self.process_command,
                              queue=self.command_q, no_ack=False)
        channel.start_consuming()

    def process_command(self, ch, method, props, body):
        """server中的命令执行函数"""
        ch.basic_ack(delivery_tag=method.delivery_tag)
        body = self.decode_body(body)
        args, kwargs = body
        rtk = method.routing_key.replace(self.command_prefix, "")
        buf = rtk.split("@")
        rtk = buf[0]
        if len(buf) > 1:
            id = buf[1]
            if self.command_q != id:
                print "no match id"
                return
        fn = self.command_fun.get(rtk)
        if fn:
            result = fn(*args, **kwargs)
            rbody = result
            self.push_msg(qid=self.command_q, topic="", msg=rbody, reply_id=props.correlation_id, session=ch,
                          to=props.reply_to)

    def command(self, name=None, *args, **kwargs):
        """work frame客户端命令调用函数"""
        id = kwargs.get("id")
        try:
            kwargs.pop("id")
        except:
            pass
        if name and name in self.command_fun:
            topic = "{0}{1}".format(self.command_prefix, name)
            if id:
                topic = "{0}{1}@{2}".format(self.command_prefix, name, id)
            qid = "command_{0}.{1}.{2}".format(self.command_q, name, uuid.uuid4())
            self.create_queue(qid, exclusive=True, auto_delete=True, )
            self.push_msg(qid, topic=topic, msg=(args, kwargs), ttl=15)
            return qid

    def get_response(self, qid, timeout=0):
        """work frame 客户端结果获取函数"""
        if timeout:
            time.sleep(timeout)
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

    def get_last_version(self, service=None, timeout=5):
        r = self.command("get_service_version", service=service)
        data = self.get_response(r, timeout=timeout, )
        last_dict = {}
        for id in data:
            for service in data[id]:
                t = last_dict.get(service)
                if t and data[id][service]["version"] > t[0]:
                    last_dict[service] = [data[id][service]["version"], data[id][service]["path"], id]
                else:
                    last_dict.setdefault(service, [data[id][service]["version"], data[id][service]["path"], id])
        return last_dict

    @Command
    def system(self, cmd):
        output = os.popen(cmd)
        data = output.read()
        output.close()
        return data

    @Command
    def restart_service(self):
        self.restart(1)
        return 'restart ok'

    @Command
    def get_service_version(self, service=None):
        rdata = {}
        if not service:
            for i in self.loaded_services['service_pkg']:
                data = copy.deepcopy(self.loaded_services['service_pkg'][i])
                data.pop("services")
                rdata.setdefault(i, data)
        else:
            data = copy.deepcopy(self.loaded_services['service_pkg'][service])
            data.pop("services")
            rdata = {service: data}
        return rdata

    @Command
    def zip_pkg(self, service_pkg):
        print '--- enter zip ---'
        pkg_path = self.loaded_services['service_pkg'][service_pkg]['path']
        tmp = BytesIO()
        cwd = os.getcwd()
        os.chdir(pkg_path)
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk('.'):
                for f in files:
                    if f.split('.')[-1] != 'pyc':
                        print os.path.join(root, f)
                        z.write(os.path.join(root, f), compress_type=zipfile.ZIP_DEFLATED)

        res = tmp.getvalue()
        tmp.close()
        os.chdir(cwd)
        print '--- leave zip ---'
        return res

    @Command
    def update_pkg(self, from_server_id, service_pkg, timeout=5):
        """被更新服务端发起"""
        print '--- Enter update pkg ---'
        if from_server_id == self.command_q:
            return 'I am the source code'
        r = self.command('zip_pkg', service_pkg, id=from_server_id)
        data = self.get_response(r, timeout=timeout)
        if not data:
            return 'ERR: No Zip Content from get_response'

        content = data[from_server_id]
        self_server_path = self.loaded_services.get('service_pkg').get(service_pkg, {}).get('path')
        if not self_server_path:
            return 'ERR: No Service In Server: {}, Cannot update'.format(self.command_q)
        if not content:
            return 'ERR: No Zip Content'

        tmp = BytesIO()
        tmp.write(content)
        z = zipfile.ZipFile(tmp, 'r', zipfile.ZIP_DEFLATED)

        cwd = os.getcwd()
        os.chdir(self_server_path)
        print 'zip file list'
        for i in z.namelist():
            print i
        z.extractall()
        z.close()
        tmp.close()
        os.chdir(cwd)
        print '--- Leave update pkg ---'
        return 'update ok'

    def update_service(self, service_pkg, version=None, id=None, timeout=5):
        fid = None
        if not version:
            v = self.get_last_version(service_pkg, ).get(service_pkg)
            if v:
                fid = v[2]
        else:
            r = self.command("get_service_version", service=service_pkg)
            data = self.get_response(r, timeout=timeout, )
            for ids in data:
                for service in data[id]:
                    if version == data[id][service]["version"]:
                        fid = ids
                        break
        if fid:
            r = self.command("update_pkg", fid, service_pkg, id=id, timeout=timeout)
            data = self.get_response(r, timeout=timeout)
            return data


def main():
    AMQ_URI = "amqp://user:3^)NB@101.199.126.121:5672/api"
    w = WORK_FRAME("test", auri=AMQ_URI)
    w.start()
    # w.command("system", "ls -la /")


if __name__ == '__main__':
    main()
