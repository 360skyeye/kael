# -*- coding: utf-8 -*-
import click
from gevent.wsgi import WSGIServer
from web_admin import app


@click.group()
def web_cli():
    """
    This shell command start kael web admin for Kael applications.

    Example usage:

    \b
        $ kael-web dev (For development)
    """
    pass


@web_cli.command('run', short_help='start a kael web admin for production')
@click.option('-s', help='Run a simple server.', is_flag=True)
@click.option('--conf', '-c', help='supervior', is_flag=True)
@click.option('-p', help='Port, default 5000', default=5000)
def web_run():
    pass


@web_cli.command('dev', short_help='start a kael web admin for development')
@click.option('-p', help='Dev Server Port, default 5000', default=5000)
@click.option('--amqp', '-a', help='AMQP_URI, default in flask setting', default=app.config.get('AMQP_URI'))
@click.option('--redis', '-r', help='REDIS_URL, default in flask setting', default=app.config.get('REDIS_URL'))
def dev(p, amqp, redis):
    """
    Example usage:

    \b
        $ kael-web dev -p 5000
        $ kael-web dev -p 5000 -a 'amqp://user:****@localhost:5672/api' -r 'redis://:***@localhost:6379/14'
    """
    app.config['AMQP_URI'] = amqp
    app.config['REDIS_URL'] = redis

    print 'AMQP_URI:', str(amqp)
    print 'REDIS_URL:', str(redis)

    app.debug = True
    print app.url_map
    print ' * Running on 0.0.0.0:{} (Press CTRL+C to quit)'.format(p)
    server = WSGIServer(("0.0.0.0", p), app)
    server.serve_forever()


def web_main():
    web_cli()


if __name__ == '__main__':
    web_main()
