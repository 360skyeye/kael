# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/5/20

from gevent.pool import Pool
import gevent.monkey
from microservice import micro_server
import os
import uuid
import inspect

gevent.monkey.patch_all()


def Command(func):
    def warp(cls, *args, **kwargs):
        # cls.actions.setdefault(func.__name__,func)
        return func(cls, *args, **kwargs)

    return warp


class WORK_FRAME(micro_server):
    command_fun = {}

    def __init__(self, name, app=None, channel="center", lock=False, auri=None):
        super(WORK_FRAME, self).__init__(name, app=app, channel=channel, auri=auri, lock=lock)
        self.command_q = "{0}-{1}".format(self.name, self.id)
        self.create_queue(self.command_q, ttl=15)
        self.command_prefix = "skyeye-rpc-{0}.".format(self.name)
        self.join(self.command_q, "{0}*".format(self.command_prefix))
        self.init_command()
        self.command_pool = Pool(100)

    def start(self, process_num=2, daemon=True):
        # print self.command_q
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
            rbody = self.encode_body(result)
            # print rbody
            self.push_msg(qid=self.command_q, topic="", msg=rbody, reply_id=props.correlation_id, session=ch,
                          to=props.reply_to)
            # print props.reply_to
            # self.pool.spawn(fn,*args,**kwargs)

    def command(self, name=None, *args, **kwargs):
        if name and name in self.command_fun:
            topic = "{0}{1}".format(self.command_prefix, name)
            qid = "command_{0}.{1}.{2}".format(self.command_q, name, uuid.uuid4())
            self.create_queue(qid, exclusive=True, auto_delete=True, )
            self.push_msg(qid, topic=topic, msg=(args, kwargs), ttl=15)
            return qid

    def get_response(self, qid, timeout=5):
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

    @Command
    def system(self, cmd):
        output = os.popen(cmd)
        data = output.read()
        output.close()
        return data


def main():
    AMQ_URI = "amqp://user:3^)NB@101.199.126.121:5672/api"
    w = WORK_FRAME("test", auri=AMQ_URI)
    w.start()
    # w.command("system", "ls -la /")


if __name__ == '__main__':
    main()