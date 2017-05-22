#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/05/18
from mq_service.microservice import micro_server
from mq_service.work_frame import WORK_FRAME
import click
import sys
import os

path = os.path.abspath(os.path.dirname(__file__))
if path not in sys.path:
    sys.path.insert(0, path)
path = os.path.split(path)
if path not in sys.path:
    sys.path.insert(0, path[0])

AMQ_URI = "amqp://user:3^)NB@101.199.126.121:5672/api"


@click.group()
def cli():
    pass


@cli.command()
def s():
    server = micro_server("s1", auri=AMQ_URI)

    @server.service("hha")
    def h(s):
        print "HHHHH", s, os.getpid()
        return {"b": s}

    server.start(4, daemon=False)
    r = server.hha(123123)
    print server.hha.src
    print "--------------", r
    print "done"


@cli.command()
def c():
    server = micro_server("s1", auri=AMQ_URI)
    r = server.hha(s=12312, qid="a")
    print server.hha.src
    print r


@cli.command()
def p():
    w = WORK_FRAME("test", auri=AMQ_URI)
    w.start()
    # server = micro_server("serive_webservice", auri=AMQ_URI)
    # print server.web_proxy.src
    # while 1:
    # server.push_msg(qid="hahah",topic="test",to="a")
    # print server.pull_msg("a", limit=3)


if __name__ == "__main__":
    cli()
