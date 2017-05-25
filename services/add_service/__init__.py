#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@version: 
@author:
@time: 2017/5/25 16:07
"""


def run(a, b):
    return t(a) + y(b)


def t(a):
    return a


def y(b):
    return b


class TMP(object):
    def __init__(self):
        self.count = 0


if __name__ == '__main__':
    print run(1, 2)
