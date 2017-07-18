# -*- coding: utf-8 -*-
import os
import click
from gevent.wsgi import WSGIServer
from kael.web_admin import app
from kael.daemon import Daemon

AMQ_URI = os.environ.get('KAEL_AURI')


@click.group()
def web_cli():
    """
    This shell command start kael web admin for Kael applications.

    Example usage:

    \b
        $ kael-web dev (For development)
        $ kael-web run (For production)

        use --help for more information
    """
    pass


class WebServer(Daemon):
    def run(self, kael_amqp, port):
        app.config['AMQP_URI'] = kael_amqp
        server = WSGIServer(("0.0.0.0", port), app)
        server.serve_forever()


@web_cli.command('run', short_help='start a kael web admin for production')
@click.option('--port', '-p', help='Port, default 5000', default=5000)
@click.option('--pid', help='Pid file', default='kael.pid')
@click.option('--command', '-c', help='Command, [start | stop | restart | status]',
              type=click.Choice(['start', 'stop', 'restart', 'status']))
@click.option('--kael_amqp', '-a', help='AMQP_URI, default in flask setting', default=None)
def run(pid, command, port, kael_amqp):
    """
     Example usage:

    \b
        $ kael-web run --command start
        $ kael-web run -c start --kael_amqp 'amqp://user:****@localhost:5672/api'

    """
    if not command:
        raise click.BadParameter('Use --command to set. [start | stop | restart | status]')

    if command != 'stop':
        kael_amqp = kael_amqp or AMQ_URI or app.config.get('AMQP_URI')
        app.config['AMQP_URI'] = kael_amqp
        print '\n', 'AMQP_URI:', str(kael_amqp), '\n'
        if not kael_amqp:
            raise click.BadParameter('Use --kael_amqp to set AMQP_URI (AMQP_URI not set)')

        print 'pid:', pid
        if command != 'status':
            print app.url_map
            print ' * Running on 0.0.0.0:{}'.format(port)

    ws = WebServer(pidfile=pid)
    ws.__getattribute__(command)(kael_amqp, port)


@web_cli.command('dev', short_help='start a kael web admin for development')
@click.option('-p', help='Dev Server Port, default 5000', default=5000)
@click.option('--kael_amqp', '-a', help='AMQP_URI, default in flask setting', default=None)
def dev(p, kael_amqp):
    """
    Example usage:

    \b
        $ kael-web dev
        $ kael-web dev -p 5000 --kael_amqp 'amqp://user:****@localhost:5672/api'
    """
    kael_amqp = kael_amqp or AMQ_URI or app.config.get('AMQP_URI')
    app.config['AMQP_URI'] = kael_amqp
    print '\n', 'AMQP_URI:', str(kael_amqp), '\n'

    if not kael_amqp:
        raise click.BadParameter('Use --kael_amqp to set AMQP_URI (AMQP_URI not set)')
    app.debug = True

    print app.url_map
    print ' * Running on 0.0.0.0:{} (Press CTRL+C to quit)'.format(p)
    server = WSGIServer(("0.0.0.0", p), app)
    server.serve_forever()


def web_main():
    web_cli()


if __name__ == '__main__':
    web_main()
