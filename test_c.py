# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/5/22
from kael.producer import Producer


def main():
    AMQ_URI = "amqp://user:3^)NB@101.199.126.121:5672/api"
    P = Producer("test", auri=AMQ_URI, )
    P.load_schema("forms.yml")
    data = {"event": "dasdad", "ip": "12.13.12.1", "timestamp": "2013-03-25 21:39:35"}
    P.pub("honey.ioc", data, schema_type="scan_ip")


if __name__ == '__main__':
    main()
