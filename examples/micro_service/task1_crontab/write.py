#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@version: 
@author:
@time: 2017/5/25 16:07
"""

import random


def sql():
    """do someting"""
    with open('cron_write.log', 'a') as f:
        f.writelines(str(random.choice(range(10))))


if __name__ == '__main__':
    sql()
