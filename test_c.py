# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/5/22
from mq_service.work_frame import WORK_FRAME
import time


def main():
    AMQ_URI = "amqp://user:3^)NB@101.199.126.121:5672/api"
    w = WORK_FRAME("test", auri=AMQ_URI)
    # w.start()
    r = w.command("system", "ls -la /")
    print r
    time.sleep(5)
    print w.get_response(r)


if __name__ == '__main__':
    main()
