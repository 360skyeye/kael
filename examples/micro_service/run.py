#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import time
from pprint import pprint

import click

from kael.microservice import micro_server
from kael.work_frame import WORK_FRAME

file_path = os.path.abspath(os.path.dirname(__file__))
if file_path not in sys.path:
    sys.path.insert(0, file_path)
path = os.path.split(file_path)
if path not in sys.path:
    sys.path.insert(0, path[0])

AMQ_URI = os.environ.get('AMQ_URI')


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

    server.start_service(4, daemon=False)
    r = server.hha(123123)
    print server.hha.src
    print "--------------", r
    print "done"
    print server.services


@cli.command()
def c():
    server = micro_server("s1", auri=AMQ_URI)
    r = server.hha(s=12312, qid="a")
    print server.hha.src
    print r


@cli.command()
def p():
    conf_dir = os.path.join(file_path, 'setting.yaml')
    w = WORK_FRAME("test", auri=AMQ_URI, service_group_conf=conf_dir)
    w.frame_start()


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
def status():
    print '-' * 10, 'service', '-' * 10
    server = WORK_FRAME("test", auri=AMQ_URI)
    r = server.command("get_pkg_version", pkg_type='service')
    pprint(server.get_response(r))
    print '\n\n', '-' * 10, 'crontab', '-' * 10
    r = server.command("get_pkg_version", pkg_type='crontab')
    pprint(server.get_response(r))
  
  
@cli.command()
def restart_service():
    server = WORK_FRAME("test", auri=AMQ_URI)
    r = server.command("restart_service", not_id='test-8bee87c0-69de-45d8-919b-6a5014eb00b2')
    print server.get_response(r, timeout=5)
    
    
@cli.command()
def restart_crontab():
    server = WORK_FRAME("test", auri=AMQ_URI)
    r = server.command("restart_crontab")
    print server.get_response(r, timeout=5)


@cli.command()
def update_s():
    service = 'time'
    server = WORK_FRAME("test", auri=AMQ_URI)
    r = server.command("get_pkg_version")
    pprint(server.get_response(r, timeout=5, ))
    pprint(server.update_service(service))


@cli.command()
def update_c():
    crontab = 'print'
    server = WORK_FRAME("test", auri=AMQ_URI)
    r = server.command("get_pkg_version", pkg_type='crontab')
    pprint(server.get_response(r, timeout=5, ))
    pprint(server.update_crontab(crontab, version=1.0))


@cli.command()
def install():
    server = WORK_FRAME("test", auri=AMQ_URI)
    service = 'calculate'
    pprint(server.get_last_version(service))
    pprint(server.install_service(service, './caccu'))


# cron tab
@cli.command()
def scron():
    """micro server crontab"""
    server = micro_server("test", auri=AMQ_URI)
    server.add_crontab(cron_name='haha', command='echo 2', time_str='* * * * *')
    server.start_crontab()
    print '-' * 100
    print 'USER ALL CRONTAB'
    pprint(server.cron_manage.user_cron_jobs())
    print '-' * 100


@cli.command()
def wfcron():
    """work frame crontab"""
    server = WORK_FRAME("test", auri=AMQ_URI)
    pprint(server.get_all_crontab_status())
    
    
if __name__ == "__main__":
    cli()
