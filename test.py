#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/05/18
import os
import sys
import time

import click

from kael.microservice import micro_server
from kael.work_frame import WORK_FRAME

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
    print server.services

    time.sleep(2)
    # server.stop()
    print 'stop & restart'
    print '-' * 20

    print server.services
    # time.sleep(3)
    server.restart(2, daemon=False)
    r = server.hha(123)
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
    cur_dir = os.path.realpath('.')
    conf_dir = os.path.join(cur_dir, 'services_default', 'setting.yaml')
    print conf_dir
    w = WORK_FRAME("test", auri=AMQ_URI, service_group_conf=conf_dir)
    w.frame_start()
    # server = micro_server("serive_webservice", auri=AMQ_URI)
    # print server.web_proxy.src
    # while 1:
    # server.push_msg(qid="hahah",topic="test",to="a")
    # print server.pull_msg("a", limit=3)


@cli.command()
def pc():
    server = WORK_FRAME("test", auri=AMQ_URI)
    print server.calculate__add(10, 20)
    print server.calculate__minus(10, 20)
    print server.time__add(1)

    r = server.command("restart_service")
    print r
    time.sleep(3)
    print server.get_response(r)


@cli.command()
def z():
    server = WORK_FRAME("test1", auri=AMQ_URI)
    # r = server.command('zip_pkg', '/home/zhangmengyang/project/mq-service/services_default/')
    # print r
    # time.sleep(3)
    # print server.get_response(r)
    # latest = server.get_last_version()
    # from_id = latest[service][2]
    # to_id = 'test-ce3b94fc-e42a-4ba7-b9dd-c6df2449c852'
    # server.command('update_pkg', 'test1-00cc014b-23e7-4c04-bed1-1cf578f70c8d', service, timeout=5)
    service = 'calculate'
    print server.get_last_version(service)
    print server.update_service(service)


if __name__ == "__main__":
    cli()
