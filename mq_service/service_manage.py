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
    """
    1.根据配置的service_group名称，进入服务包读取配置，导出配置中发布的服务函数及配置
    2.进入服务包中，根据服务自己的配置，导出服务函数
    """
    Services = {'services': {}}
    service_base_name_exist = set()
    service_group_dir = os.path.join(base_dir, service_group)
    if not os.path.exists(service_group_dir):
        raise ImportError('Service_Group: "{}" NOT EXIST'.format(service_group))

    # 1 读取服务包配置
    pkg_group_setting_file = os.path.join(service_group_dir, 'setting.yaml')
    if not os.path.exists(pkg_group_setting_file):
        raise ImportError('Service_Group Setting File NOT EXIST: {}'.format(pkg_group_setting_file))
    with open(pkg_group_setting_file) as f:
        group_setting = yaml.load(f.read())

    # 2 进入服务包读取服务配置
    for pkg in os.listdir(service_group_dir):
        try:
            # 根据group配置中的enable字段导出service
            if len(pkg.split('.')) == 1 and pkg in group_setting['enable']:

                # 2.1 export setting.yaml into Services
                setting_file = os.path.join(service_group_dir, pkg, 'setting.yaml')
                with open(setting_file) as f:
                    s = yaml.load(f.read())
                    if s['service_base_name'] in service_base_name_exist:
                        logging.error('Registering from {}'.format(setting_file))
                        raise Exception('Service Name Already Existed: {0}'.format(s['service_base_name']))
                    else:
                        service_base_name_exist.add(s['service_base_name'])
                        # todo 根据装饰器生成各种service_name cal-add cal-mul...
                        gen_service_name = s['service_base_name']
                        Services['services'][gen_service_name] = s

                # 2.2 export run function into Services
                module = __import__('services_default.{0}.__init__'.format(pkg), fromlist='dummy')
                run = getattr(module, 'run')
                Services['services'][gen_service_name]['function'] = run
                Services['services'][gen_service_name]['service_pkg'] = pkg
        except Exception as e:
            logging.exception(e)

    Services.update(group_setting)
    return Services

if __name__ == '__main__':
    pprint(get_service_group())