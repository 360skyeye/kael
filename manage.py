# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
from gevent.wsgi import WSGIServer
from web_admin import app


def main():
    app.debug = True
    print app.url_map
    server = WSGIServer(("0.0.0.0", 5000), app)
    server.serve_forever()


if __name__ == '__main__':
    main()
