# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/5/20

from gevent.pool import Pool
import gevent.monkey
from microservice import micro_server
import os

gevent.monkey.patch_all()


def command(cls):
    '''''cls 必须实现acquire和release静态方法'''

    def _deco(func):
        cls.command_fun.setdefault(func.__name__, func)

        def __deco():
            pass

        return __deco

    return _deco


class WORK_FRAME(micro_server):
    command_fun = {}

    def __init__(self, name, app=None, channel="center", lock=False, auri=None):
        super(WORK_FRAME, self).__init__(name, app=app, channel=channel, auri=auri, lock=lock)
        self.command_q = self.id
        self.create_queue(self.id)
        self.command_prefix = "skyeye-rpc-{0}.".format(self.name)
        self.join(self.command_q, "{0}*".format(self.command_prefix))
        self.command_pool = Pool(100)

    def start(self, process_num=2, daemon=True):
        print self.command_q
        super(WORK_FRAME, self).start(process_num, daemon=daemon)
        channel = self.connection.channel()
        channel.basic_consume(self.process_command,
                              queue=self.command_q, no_ack=False)
        channel.start_consuming()
        # self.pool.join()

    def process_command(self, ch, method, props, body):
        ch.basic_ack(delivery_tag=method.delivery_tag)
        body = self.decode_body(body)
        args, kwargs = body
        rtk = method.routing_key.replace(self.command_prefix, "")
        fn = self.command_fun.get(rtk)
        if fn:
            result = fn(*args, **kwargs)
            # self.pool.spawn(fn,*args,**kwargs)

    def command(self, name=None, *args, **kwargs):
        if name and name in self.command_fun:
            topic = "{0}{1}".format(self.command_prefix, name)
            self.push_msg(self.command_q, topic=topic, msg=(args, kwargs))


@command(WORK_FRAME)
def system(cmd):
    print os.system(cmd)


def main():
    AMQ_URI = "amqp://user:3^)NB@101.199.126.121:5672/api"
    w = WORK_FRAME("test", auri=AMQ_URI)
    w.command("system", "ls -la /")
    w.start()


if __name__ == '__main__':
    main()
