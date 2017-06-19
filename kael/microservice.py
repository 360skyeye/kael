#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@version:
@author:
@time: 2017/5/10
"""
import inspect
import logging
import os
# import signal
import sys
import time
from functools import wraps
from multiprocessing import Process
from uuid import uuid4

import fcntl
import gevent.monkey
import pika
from gevent.pool import Pool
from termcolor import colored

from kael import MQ
from kael.cron import Cron

gevent.monkey.patch_all()


class micro_server(MQ):
    def __init__(self, name, app=None, channel="center", extype="topic", lock=False, auri=None):
        super(micro_server, self).__init__(app=app, channel=channel, extype=extype, auri=auri)
        self.name = name
        self.app = app
        self.lock = lock
        self.services = {}
        self.cron_manage = Cron()  # {'<cron_name>': [{'time_str': '1 * * * *', 'command': '/bin/bash xx.sh'}]}
        self.id = str(uuid4())
        self.pro = {}
        self.pid = None
        self.LOCK_PATH = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "{0}.lock".format(self.name))
        self.is_running = False
        self.services.setdefault("man", self.man)
        self.register_all_service_queues()

    def single_instance(self):
        try:
            self.fh = open(self.LOCK_PATH, 'w')
            fcntl.lockf(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except EnvironmentError:
            if self.fh is not None:
                self.is_running = True
            else:
                raise

    def start_service(self, n=1, daemon=True):
        """启动服务"""
        print 'MICRO START SERVICE', '\n', 80 * '-'
        # 启动服务
        self.register_all_service_queues()
        for i in range(n):
            pro = Process(target=self.proc)
            pro.daemon = daemon
            pro.start()
            self.pro.setdefault(pro.pid, pro)

    def stop_service(self):
        """停止服务"""
        # 停止所有子进程
        for pid, pro in self.pro.iteritems():
            try:
                pro.terminate()
            except Exception as e:
                logging.exception(e)
    
    def start_crontab(self):
        """设置定时任务"""
        print 'MICRO START CRONTAB', '\n', 80 * '-'
        self.active_crontabs()
 
    def stop_crontab(self):
        """删除定时任务"""
        self.cron_manage.clean_added_jobs()

    # region crontab
    def add_crontab(self, cron_name, command, time_str):
        """
        添加单条crontab，供手动单独添加使用。
        :param cron_name:   定时任务名
        :param command:     定时任务命令
        :param time_str:    定时任务时间
        :return bool
        """
        return self.cron_manage.add(command=command, time_str=time_str, job_name=cron_name)
        
    def del_crontab(self, cron_name):
        """
        删除待添加的定时任务，供手动单独删除使用。
        :param cron_name: 删除待添加任务中的定时任务
        :return: bool
        """
        return self.cron_manage.del_to_add_job(cron_name)
        
    def set_crontabs(self, cron_name, jobs):
        """
        供批量添加修改使用。替换已有，增加未有。(可供work frame调用)
        :param cron_name:   定时任务名
        :param jobs:        定时任务列表 [{'command':'', 'time_str':'' }]
        :return bool
        cron_name下的任务，只要有写错的(time_str)，则cron整体都不能添加，返回False，应修改至全部正确
        """
        return self.cron_manage.set_to_add_jobs(job_name=cron_name, jobs=jobs)

    def active_crontabs(self):
        """将预添加的定时任务写入系统，没有则新增，有则删除旧再新增"""
        self.cron_manage.micro_service_active_jobs()
    # endregion
        
    def proc(self):
        if self.lock:
            self.single_instance()
        if self.is_running:
            print "server[{0}] is already running on {1} mode.".format(colored(self.name, "green"),
                                                                       colored("single", "red"))
            return
        self.connection = self.connect()
        self.pool = Pool(100)
        for service, fn in self.services.items():
            con = self.__make_consumer(service, fn)
            self.pool.spawn(con, )
        self.pool.join()
        return

    def __make_consumer(self, service_name, fn):
        def consumer():
            print "server[{2}]        service [{0: ^48}]   @  pid:{1} ".format(self.service_qid(service_name),
                                                                               colored(os.getpid(), "green"),
                                                                               colored(self.name, "green"))
            try:
                channel = self.connection.channel()
            except:
                self.connection = self.connect()
                channel = self.connection.channel()
            channel.basic_qos(prefetch_count=1)
            gfn = self.make_gevent_consumer(fn)

            # """Using the Blocking Connection to consume messages from RabbitMQ"""
            channel.basic_consume(gfn, queue=self.service_qid(service_name), no_ack=False)
            try:
                channel.start_consuming()
            except Exception:
                self.connection = self.connect()
                channel = self.connection.channel()
                channel.start_consuming()
            print colored("---channel-close---", "red")

        return consumer

    def make_gevent_consumer(self, fn):
        def haha(*args, **kwargs):
            args = list(args[:])
            ch, method, props, body = args[0:4]
            body = self.decode_body(body)
            args[3] = body
            ch.basic_ack(delivery_tag=method.delivery_tag)
            f = self.make_co(fn)
            greend = self.pool.spawn(f, *args, **kwargs)
            return greend

        return haha

    def make_co(self, fn):
        def warp(*args, **kwargs):
            ch, method, props, body = args[0:4]
            ctx = {"ch": ch, "method": method, "props": props, "body": body}
            dargs, dkwargs = body
            fargs = inspect.getargspec(fn).args
            if "ctx" in fargs:
                dkwargs.update({"__CTX": ctx})
            rtdata = fn(*dargs, **dkwargs)
            ch.basic_publish(exchange='',
                             routing_key=props.reply_to,
                             properties=pika.BasicProperties(correlation_id=props.correlation_id),
                             body=self.encode_body(rtdata))

        return warp

    def service_qid(self, service_name):
        qid = "{0}.{1}".format(self.name, service_name)
        return qid

    def register_all_service_queues(self):
        """为所有服务函数创建queue"""
        for service, fn in self.services.items():
            qid = self.service_qid(service)
            self.create_queue(qid, exclusive=False, auto_delete=True, )
            self.join(qid, qid)

    def service(self, service_name, *args, **kwargs):
        def process(fn):
            self.services.setdefault(service_name, fn)

            @wraps(fn)
            def wrapper(*args, **kwargs):
                pass

            return wrapper

        return process

    def rpc(self, service):
        def maker(*args, **kwargs):
            qid = kwargs.get("qid")
            if qid:
                qid = kwargs.pop("qid")
                return self.push_msg(qid, "", (args, kwargs), to=self.service_qid(service), )
            else:
                qid = "rpc_{0}.{1}.{2}".format(self.name, service, uuid4())
                self.create_queue(qid, exclusive=True, auto_delete=True, )
                self.push_msg(qid, "", (args, kwargs), to=self.service_qid(service), )
                while 1:
                    ctx = self.pull_msg(qid=qid, )
                    if not ctx:
                        time.sleep(1)
                        continue
                    else:
                        return ctx[-1][-1]

        return maker

    def __getattr__(self, item):
        try:
            r = self.create_queue(self.service_qid(item), passive=True)
        except:
            return super(micro_server, self).__getattribute__(item)
        if r:
            rt = self.rpc(item)
            rt.src = self.rpc("man")(item)
            return rt
        else:
            super(micro_server, self).__getattribute__(item)

    def man(self, service):
        if self.services.get(service, ):
            return inspect.getsource(self.services.get(service, ))


def main():
    pass


if __name__ == '__main__':
    main()
