# -*- coding: utf-8 -*-

from kael.producer import Producer
import os

AMQ_URI = os.environ.get('AMQ_URI')


def main():
    P = Producer("test", auri=AMQ_URI, )
    P.load_schema("forms.yml")
    data = {"event": "dasdad", "ip": "12.13.12.1", "timestamp": "2013-03-25 21:39:35"}
    P.pub("honey.ioc", data, schema_type="scan_ip")


if __name__ == '__main__':
    main()
