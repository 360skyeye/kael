#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@version: 
@author:
@time: 2017/5/25 16:07
"""
import datetime
import time


def add(a, b=1):
    return time.time() + b


def transfer(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    print add(1, 2)
    print transfer(datetime.datetime.now())
