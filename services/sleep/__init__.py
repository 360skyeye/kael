#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@version: 
@author:
@time: 2017/5/25 16:07
"""

import datetime
import time


def sleep_function(m, n):
    print 'start@', datetime.datetime.now()
    time.sleep(5)
    print 'end@', datetime.datetime.now()
    return str(datetime.datetime.now())


run = sleep_function
