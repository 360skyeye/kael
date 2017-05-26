#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@version: 
@author:
@time: 2017/5/25 17:04
"""
from pprint import pprint

from mq_service.service_manage import get_service_group
Services = get_service_group()
# Services = get_service_group(service_group='services_s1')
# Services = get_service_group(service_group='not_exsit')
pprint(Services)

print 30*'-'
print Services['add']['function'](6, 2)
print Services['sleep']['function'](1, 1)
