#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@version: 
@author:
@time: 2017/5/26 14:26
"""
import logging
import os
from pprint import pprint

import yaml

cur_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.sep.join(cur_dir.split(os.path.sep)[:-1])


def get_service_group(service_group='services_default'):
    """根据配置的service_group名称，进入服务包读取配置，导出配置中发布的服务函数及配置"""
    Services = {}
    service_group_dir = os.path.join(base_dir, service_group)
    if not os.path.exists(service_group_dir):
        raise ImportError('Service_Group: "{}" NOT EXIST'.format(service_group))
    for pkg in os.listdir(service_group_dir):
        try:
            if len(pkg.split('.')) == 1:
                # 1 export setting.yaml into Services
                setting_file = os.path.join(service_group_dir, pkg, 'setting.yaml')
                with open(setting_file) as f:
                    s = yaml.load(f.read())
                    if s['service_name'] in Services:
                        logging.error('Registering from {}'.format(setting_file))
                        raise Exception('Service Name Already Existed: {0}'.format(s['service_name']))
                    else:
                        Services[s['service_name']] = s

                # 2 export run function into Services
                module = __import__('services_default.{0}.__init__'.format(pkg), fromlist='dummy')
                run = getattr(module, 'run')
                Services[s['service_name']]['function'] = run
        except Exception as e:
            logging.exception(e)
    return Services

if __name__ == '__main__':
    pprint(get_service_group())