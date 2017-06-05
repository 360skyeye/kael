# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/5/20

import inspect
import os
import uuid

import gevent.monkey
from gevent.pool import Pool

from microservice import micro_server
from mq_service.service_manage import get_service_group

gevent.monkey.patch_all()


def Command(func):
    def warp(cls, *args, **kwargs):
        # cls.actions.setdefault(func.__name__,func)
        return func(cls, *args, **kwargs)

    return warp


class WORK_FRAME(micro_server):
    command_fun = {}

    def __init__(self, name, app=None, channel="center", lock=False, auri=None, service_group=None):
        super(WORK_FRAME, self).__init__(name, app=app, channel=channel, auri=auri, lock=lock)
        self.command_q = "{0}-{1}".format(self.name, self.id)
        self.create_queue(self.command_q, ttl=15)
        self.command_prefix = "skyeye-rpc-{0}.".format(self.name)
        self.join(self.command_q, "{0}*".format(self.command_prefix))
        self.init_command()
        self.command_pool = Pool(100)
        self.init_service(service_group)

    def init_service(self, service_group):
        self.loaded_services = get_service_group(service_group)
        for service_name, value in self.loaded_services['services'].iteritems():
            fn = value['function']
            self.services.setdefault(service_name, fn)

    def frame_start(self, process_num=2, daemon=True):
        """框架启动"""
        print 'WORK FRAME START'
        # print self.command_q
        self.start(process_num, daemon=daemon)
        channel = self.connection.channel()
        channel.basic_consume(self.process_command,
                              queue=self.command_q, no_ack=False)
        channel.start_consuming()
        # self.pool.join()

    def process_command(self, ch, method, props, body):
        """server中的命令执行函数"""
        ch.basic_ack(delivery_tag=method.delivery_tag)
        body = self.decode_body(body)
        args, kwargs = body
        rtk = method.routing_key.replace(self.command_prefix, "")
        fn = self.command_fun.get(rtk)
        if fn:
            result = fn(*args, **kwargs)
            rbody = result
            # print rbody
            self.push_msg(qid=self.command_q, topic="", msg=rbody, reply_id=props.correlation_id, session=ch,
                          to=props.reply_to)
            # print props.reply_to
            # self.pool.spawn(fn,*args,**kwargs)

    def command(self, name=None, *args, **kwargs):
        """work frame客户端命令调用函数"""
        if name and name in self.command_fun:
            topic = "{0}{1}".format(self.command_prefix, name)
            qid = "command_{0}.{1}.{2}".format(self.command_q, name, uuid.uuid4())
            self.create_queue(qid, exclusive=True, auto_delete=True, )
            self.push_msg(qid, topic=topic, msg=(args, kwargs), ttl=15)
            return qid

    def get_response(self, qid, timeout=5):
        """work frame 客户端结果获取函数"""
        # time.sleep(timeout)
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

    def get_last_version(self,service=None):
        r=self.command("get_service_version",)

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
    def get_service_version(self,service=None):
        data={"id":self.command_q,}
        rdata={}
        if not service:
            for i in self.loaded_services['service_pkg']:
                rdata.setdefault(i,self.loaded_services['service_pkg'][i])
        else:
            rdata={service:self.loaded_services['service_pkg'][service]}
        data["services"] = rdata
        return data




def main():
    AMQ_URI = "amqp://user:3^)NB@101.199.126.121:5672/api"
    w = WORK_FRAME("test", auri=AMQ_URI)
    w.start()
    # w.command("system", "ls -la /")


if __name__ == '__main__':
    main()
