# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
from gevent.wsgi import WSGIServer
from kael.web_admin import app


def main():
    print '\n', 'AMQP_URI:', app.config['AMQP_URI'], '\n'

    app.debug = True
    port = 5000
    print app.url_map
    print ' * Running on 0.0.0.0:{} (Press CTRL+C to quit)'.format(port)
    server = WSGIServer(("0.0.0.0", port), app)
    server.serve_forever()


if __name__ == '__main__':
    main()
