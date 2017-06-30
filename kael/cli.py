#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
import os
import json
from . import __version__
from kael.microservice import micro_server
from kael.work_frame import WORK_FRAME
from beautifultable import BeautifulTable
AMQ_URI = os.environ.get('KAEL_AURI')


@click.group()
@click.version_option(__version__)
def cli():
    """
    This shell command acts as general utility script for Kael applications.

    Example usage:

    \b
        $ export KAEL_AURI='amqp://user:****@127.0.0.1:5672/api'
        $ kael run -s
    """
    pass


@cli.command('run', short_help='Runs a development server.')
@click.option('-s', help='Run a simple server.', is_flag=True)
@click.option('-p', help='Run a custom server.')
def run(s, p):
    if s:
        server = micro_server("s1", auri=AMQ_URI)

        @server.service("foobar")
        def h(a):
            print a, os.getpid()
            return {"b": a}

        server.start_service(2, daemon=False)
    elif p:
        if not os.path.isfile(p) or os.path.splitext(p)[1] != '.yaml':
            raise click.BadParameter(
                'the param must be yaml config')
        w = WORK_FRAME(auri=AMQ_URI, service_group_conf=p)
        w.frame_start()
    else:
        raise click.UsageError(
            'Could not find other command. You can run kael run --help to see more information')


@cli.command('install', short_help='install service modules.')
@click.option('-n', help='service namespace.', default=False)
@click.option('-s', help='service module.', default=False)
@click.option('-p', help='service module install path.', default=False)
def install(n, s, p):
    server = WORK_FRAME(n, auri=AMQ_URI)
    print server.install_service(s, p)
    print server.command('_restart_service')


@cli.command('update', short_help='update service modules.')
@click.option('-n', help='service namespace.', default=False)
@click.option('-s', help='service module.', default=False)
@click.option('-v', help='service version.', default=False)
def update(n, s, v):
    if not n or not s or not v:
        raise click.BadParameter('params is wrong.')
    server = WORK_FRAME(n, auri=AMQ_URI)
    print server.update_service(s, version=float(v))
    print server.command('_restart_service')


@cli.command('restart', short_help='update service modules.')
@click.option('-n', help='service namespace.', default=False)
@click.option('-s', help='service name.', default=False)
def restart(n, s):
    if not s or not n:
        raise click.BadParameter('params is wrong.')
    server = WORK_FRAME(n, auri=AMQ_URI)
    r = server.command('_restart_service', id=s)
    print json.dumps(server.get_response(r), indent=2)


@cli.command('status', short_help='list all service modules.')
@click.option('-n', help='service namespace.', default=False)
def status(n):
    if not n:
        raise click.BadParameter('namespace is wrong.')
    server = WORK_FRAME(n, auri=AMQ_URI)
    r = server.command('_get_pkg_version')
    res = server.get_response(r)
    # print json.dumps(res, indent=2)
    for s_name in res:
        print s_name
        apps = res[s_name]
        table = BeautifulTable(max_width=100)
        table.column_headers = ['App name', 'version', 'path']
        for app in apps:
            table.append_row([app, apps[app]['version'], apps[app]['path']])
        print(table)
        print ''


@cli.command('generate', short_help='gen default service module.')
def generate():
    pass


@cli.command('client', short_help='a client for kael service.')
def client():
    pass


def main():
    cli()


if __name__ == '__main__':
    main()
