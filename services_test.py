#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@version: 
@author:
@time: 2017/5/25 17:04
"""
from pprint import pprint

from services import Services
pprint(Services)

print Services['add']['function'](6, 2)
print Services['sleep']['function'](1, 1)
