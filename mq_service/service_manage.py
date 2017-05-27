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
    2.进入服务包中，根据服务自己的配置，导出此服务发布的服务函数们
    支持两种导入策略，包或者包的名称。

    :return
    example:
    {'micro_service': 's_default',
     'service_group': 'services_default',
     'enable': ['caculate_service', 'time_service'],
     'services': {'calculate__add': {'function': <function add at 0x00000000029C7AC8>,
                                     'service_base_name': 'calculate',
                                     'service_from_pkg': 'caculate_service',
                                     'version': 1.0},
                  'calculate__minus': {'function': <function minus at 0x00000000029C7B38>,
                                       'service_base_name': 'calculate',
                                       'service_from_pkg': 'caculate_service',
                                       'version': 1.0},
                  'time__add': {'function': <function add at 0x00000000029C7EB8>,
                                'service_base_name': 'time',
                                'service_from_pkg': 'time_service',
                                'version': 1.1},
                  'time__transfer': {'function': <function transfer at 0x00000000029C7F28>,
                                     'service_base_name': 'time',
                                     'service_from_pkg': 'time_service',
                                     'version': 1.1}}}
    """
    if type(service_group).__name__ == 'module':
        service_group_dir = service_group.__path__[0]
    else:
        service_group_dir = os.path.join(base_dir, str(service_group))
    if not os.path.exists(service_group_dir):
        raise ImportError('Service_Group: "{}" NOT EXIST'.format(str(service_group)))

    pkg_group_setting_file = os.path.join(service_group_dir, 'setting.yaml')
    if not os.path.exists(pkg_group_setting_file):
        raise ImportError('Service_Group Setting File NOT EXIST: {}'.format(pkg_group_setting_file))

    service_group_name = service_group_dir.split(os.path.sep)[-1]
    Services = {'services': {}, 'service_group': service_group_name}
    service_base_name_exist = set()

    # 1 读取服务包配置
    with open(pkg_group_setting_file) as f:
        group_setting = yaml.load(f.read())
        Services.update(group_setting)

    # 2 进入服务包读取服务配置
    for pkg in os.listdir(service_group_dir):
        try:
            # 根据group配置中的enable字段导出service
            if len(pkg.split('.')) == 1 and pkg in group_setting['enable']:

                # 2.1 检查配置中每个服务的Service Base Name是否已存在
                setting_file = os.path.join(service_group_dir, pkg, 'setting.yaml')
                with open(setting_file) as f:
                    s = yaml.load(f.read())
                    if s['service_base_name'] in service_base_name_exist:
                        logging.error('Registering from {}'.format(setting_file))
                        raise Exception('Service Base Name Already Existed: {0}'.format(s['service_base_name']))
                    else:
                        service_base_name_exist.add(s['service_base_name'])

                # 2.2 找出service_pkg中发布的所有函数，添加到Services字典中
                """
                service_base_name: calculator
                publish_func_names: ['add', 'minus']
                service_name: calculator__add, calculator__minus
                """

                publish_func_names = s['publish'] or []
                module = __import__('services_default.{0}.__init__'.format(pkg), fromlist='dummy')
                current_pkg_services = {}
                try:
                    for func in publish_func_names:
                        service_name = "{0}__{1}".format(s['service_base_name'], func)
                        current_pkg_services[service_name] = dict(service_base_name=s['service_base_name'],
                                                                  service_from_pkg=pkg,
                                                                  version=s['version'],
                                                                  function=getattr(module, func))
                except Exception as e:
                    raise ImportError("{} has not function: {}. Check {}".format(pkg, func, setting_file))

                Services['services'].update(current_pkg_services)
        except Exception as e:
            logging.exception(e)

    return Services


if __name__ == '__main__':
    print 10 * '=' + 'SERVICES' + 10 * '=', '\n'

    # 1 无参数
    s1 = get_service_group()

    # 2 指定包名
    s2 = get_service_group('services_s1')

    # 3 引入包
    import services_default

    s3 = get_service_group(services_default)

    pprint(s3)
