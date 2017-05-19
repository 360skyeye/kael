# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/5/2
import pika
import uuid
from functools import wraps
import msgpack


def map_func(data, fns):
    return map(lambda x: x(data), fns)


def pipeline_func(data, fns):
    return reduce(lambda a, x: x(a), fns, data)


class MQ(object):
    def __init__(self, app=None, channel="center", extype="topic", auri=None):
        if extype not in ["topic", "fanout", "direct", "header"]:
            raise
        self.app = app
        self.extype = extype
        self.channel = channel
        self.fun_map = {}
        if auri:
            self.auri = auri
        else:
            self.auri = self.app.config.get("AMQP_URI")

        self.connection = self.connect()
        c = self.connection.channel()
        c.exchange_declare(exchange=channel,
                           type=self.extype, )
        c.close()

    def connect(self, ):
        aps = pika.URLParameters(self.auri)
        return pika.BlockingConnection(aps)

    def encode_body(self, message):
        rdata = msgpack.dumps(message)
        return rdata

    def decode_body(self, message):
        rdata = msgpack.loads(message)
        return rdata

    def session(fn):
        @wraps(fn)
        def w(self, *args, **kwargs):
            channel = self.connection.channel()
            result = fn(self, session=channel, *args, **kwargs)
            channel.close()
            return result

        return w

    @session
    def link(self, mq, topic, session=None, **kwargs):
        session.exchange_bind(destination=mq.channel, source=self.channel,
                              routing_key=topic, arguments=kwargs)

    @session
    def unlink(self, mq, topic, session=None, **kwargs):
        session.exchange_unbind(destination=mq.channel, source=self.channel,
                                routing_key=topic, arguments=kwargs)

    @session
    def join(self, qid, topic, session=None):
        session.queue_bind(exchange=self.channel,
                           queue=qid,
                           routing_key=topic, )

    @session
    def unjoin(self, qid, topic, session=None):
        session.queue_unbind(exchange=self.channel,
                             queue=qid,
                             routing_key=topic, )

    @session
    def pull_msg(self, qid, topic=None, session=None, limit=0):
        # channel.queue_delete(queuename)
        session.queue_bind(exchange=self.channel,
                           queue=qid,
                           routing_key=topic, )
        CTX = session.basic_get(queue=qid, no_ack=False)
        buffer = []
        LIMIT = limit
        while CTX[0]:
            ctx, cbp, body = CTX
            body = self.decode_body(body)
            call_funs = self.fun_map.get(topic)
            if call_funs:
                map_func(CTX, call_funs)
            buffer.append([ctx, cbp, body])
            session.basic_ack(delivery_tag=ctx.delivery_tag)
            if LIMIT:
                LIMIT -= 1
            if not limit and LIMIT:
                break
            CTX = session.basic_get(queue=qid, no_ack=False)
        return buffer

    @session
    def push_msg(self, qid, topic, msg, ttl=0, to=None, session=None):
        msg = self.encode_body(msg)
        msg_id = str(uuid.uuid4())
        session.basic_publish(exchange="" if to else self.channel,
                              routing_key=to if to else topic,
                              body=msg,
                              properties=pika.BasicProperties(expiration="%d" % (ttl * 1000) if ttl else None,
                                                              reply_to=qid,
                                                              correlation_id=msg_id,
                                                              )
                              )
        return msg_id

    @session
    def create_queue(self, qid, ttl=0, session=None, args={}, **kwargs):
        if ttl:
            args.update({"x-message-ttl": ttl * 1000})
        return session.queue_declare(queue=qid, arguments=args, **kwargs)

    @session
    def del_queue(self, qid, session=None):
        session.queue_delete(qid)

    def topic(self, topic, *args, **kwargs):
        def process(fn):
            self.fun_map.setdefault(topic, [])
            self.fun_map[topic].append(fn)

            @wraps(fn)
            def wrapper(*args, **kwargs):
                pass

            return wrapper

        return process


def main():
    print "aa"


if __name__ == '__main__':
    main()
