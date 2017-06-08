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
import signal
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

gevent.monkey.patch_all()


class micro_server(MQ):
    def __init__(self, name, app=None, channel="center", extype="topic", lock=False, auri=None):
        super(micro_server, self).__init__(app=app, channel=channel, extype=extype, auri=auri)
        self.name = name
        self.app = app
        self.lock = lock
        self.services = {}
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

    def start(self, n=1, daemon=True):
        print 'MICRO START', '\n', 30 * '-'
        # 防止子进程terminate后变为僵尸进程
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)

        self.register_all_service_queues()
        for i in range(n):
            pro = Process(target=self.proc)
            pro.daemon = daemon
            pro.start()
            self.pro.setdefault(pro.pid, pro)

    def stop(self):
        # 停止所有子进程
        for pid, pro in self.pro.iteritems():
            try:
                pro.terminate()
            except Exception as e:
                logging.exception(e)

    def restart(self, n=1, daemon=True):
        self.stop()
        # * 需要保证queue一定存在，存在可能：重启之间的时间queue被删除了，那后面监听消费queue会报错
        # 一种思路是等待一段时间，等queue自动全删完了，再重新建（依赖于auto_delete的响应时间）
        time.sleep(2)

        self.start(n, daemon)

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
