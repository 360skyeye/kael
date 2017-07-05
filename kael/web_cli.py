# -*- coding: utf-8 -*-
import click
from gevent.wsgi import WSGIServer
from kael.web_admin import app


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


@web_cli.command('run', short_help='start a kael web admin for production')
@click.option('-p', help='Port, default 5000', default=5000)
@click.option('--kael_amqp', '-a', help='AMQP_URI, default in flask setting', default=app.config.get('AMQP_URI'))
def run(p, kael_amqp):
    raise NotImplementedError('Not Implemented yet, use dev for now')


@web_cli.command('dev', short_help='start a kael web admin for development')
@click.option('-p', help='Dev Server Port, default 5000', default=5000)
@click.option('--kael_amqp', '-a', help='AMQP_URI, default in flask setting', default=app.config.get('AMQP_URI'))
def dev(p, kael_amqp):
    """
    Example usage:

    \b
        $ kael-web dev
        $ kael-web dev -p 5000 -a 'amqp://user:****@localhost:5672/api'
    """
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
