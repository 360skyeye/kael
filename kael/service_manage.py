#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@version: 
@author:
@time: 2017/5/26 14:26
"""
import logging
import os
import sys

import yaml

cur_dir = os.path.dirname(os.path.abspath(__file__))


def get_service_group(conf=None):
    """
    通过配置获取服务/定时任务包内容
    1.根据配置的path，确定底层需要执行的服务/定时任务包
    2.进入服务包中，导出各个包中发布的服务函数/定时任务

    :param conf: 配置文件地址，或者配置字典
    :return 服务函数/定时任务字典
    example:
    {
        'service_group': 'services_default',
        'service_pkg':
        {
            'calculate': {
                'path': '/data/project/mq-service/services_default/sleep_service',
                'version': 1.0,
                'services': {
                    'calculate__add': <function add at 0x00000000029C7AC8>,
                    'calculate__minus': <function minus at 0x00000000029C7B38>
                }
            },
            'time': {
                'path': '/data/project/mq-service/services_default/time_service',
                'version': 1.0,
                'services': {
                    'time__transfer': <function transfer at 0x00000000029C7F28>
                }
            }
        }
        'crontab_pkg':
        {
            'print':{
                'path':'/data/project/mq-service/services_default/task1_crontab',
                'version': 1.0,
                'crontabs':[ '1 * * * *  .....', '1 * * * *  .....' ]
            }

        }
    }"""

    Services = {'service_pkg': {}, 'crontab_pkg': {}}
    service_base_name_exist = set()
    crontab_name_exist = set()

    # 1导入服务包组的配置（配置字典 或 yaml路径）
    if type(conf) is dict:
        group_setting = conf
        service_group_dir = cur_dir

    elif type(conf) in (str, unicode):
        pkg_group_setting_file = conf
        if not os.path.exists(pkg_group_setting_file):
            raise ImportError('Service_Group Setting File NOT EXIST: {}'.format(pkg_group_setting_file))
        with open(pkg_group_setting_file) as f:
            group_setting = yaml.load(f.read())
        service_group_dir = os.path.dirname(pkg_group_setting_file)

    else:
        raise EnvironmentError('No Config of Service Group. conf={}'.format(conf))

    Services.update(group_setting)

    #  2进入服务包读取服务配置, 根据group配置中的path字段导出service
    for pkg_path in group_setting['path']:
        try:
            if not os.path.isabs(pkg_path):
                pkg_path = os.path.realpath(os.path.join(service_group_dir, pkg_path))

            # 2.1 检查配置中每个服务的Service Base Name是否已存在
            setting_file = os.path.join(pkg_path, 'setting.yaml')
            if not os.path.exists(setting_file):
                raise ImportError('Service Setting File NOT EXIST: {}'.format(setting_file))

            with open(setting_file) as f:
                s = yaml.load(f.read())
                if s.get('type') == 'service':
                    if s['service_base_name'] in service_base_name_exist:
                        logging.error('Registering from {}'.format(setting_file))
                        raise Exception('Service Base Name Already Existed: {0}'.format(s['service_base_name']))
                    else:
                        service_base_name_exist.add(s['service_base_name'])
                elif s.get('type') == 'crontab':
                    if s['crontab_name'] in crontab_name_exist:
                        logging.error('Registering from {}'.format(setting_file))
                        raise Exception('Crontab Name Already Existed: {0}'.format(s['crontab_name']))
                    else:
                        crontab_name_exist.add(s['crontab_name'])
                else:
                    raise ImportError('type: {} not support <{}>'.format(s.get('type'), setting_file))

            # 2.2 找出service_pkg中发布的所有函数，添加到Services字典中
            """
            service_base_name: calculator
            publish_func_names: ['add', 'minus']
            service_name: calculator__add, calculator__minus
            args: 
            """

            if s.get('type') == 'service':
                publish_func_names = s['publish'] or []
                sys.path.append(os.path.dirname(pkg_path))
                module = __import__('{0}'.format(os.path.basename(pkg_path)), fromlist='dummy')
                current_pkg_services = {
                    s['service_base_name']: {
                        'version': s['version'],
                        'path': pkg_path,
                        'services': {},
                        'args': s.get('args')
                    }
                }

                try:
                    for func in publish_func_names:
                        service_name = "{0}__{1}".format(s['service_base_name'], func)
                        current_pkg_services[s['service_base_name']]['services'].update(
                                {service_name: getattr(module, func)})
                except Exception as e:
                    raise ImportError(
                            "{} has not function: {}. Check {}".format(s['service_base_name'], func, setting_file))

                Services['service_pkg'].update(current_pkg_services)

            elif s.get('type') == 'crontab':
                crontab_items = s['publish'] or []

                cron_for_work_frame = []
                for i in crontab_items:
                    time_str = i[0]
                    command = 'kael-crontab run -c {} -d {}'.format(i[1], pkg_path)
                    cron_for_work_frame.append({'time_str': time_str, 'command': command})

                current_pkg_crontab = {
                    s['crontab_name']: {
                        'version': s['version'],
                        'path': pkg_path,
                        'crontabs': cron_for_work_frame
                    }
                }
                Services['crontab_pkg'].update(current_pkg_crontab)

        except Exception as e:
            logging.exception(e)

    return Services


def update_service_group(conf, service_install_path):
    """
    install service时，需要在服务包配置文件里面增加service_install_path
    :param conf: 配置文件地址，或者配置字典
    :param service_install_path:
    :return:
    """
    group_setting = None
    if type(conf) in (str, unicode):
        with open(conf) as f:
            group_setting = yaml.load(f.read())
            group_setting.setdefault('path', [])
            if service_install_path not in group_setting['path']:
                group_setting['path'].append(service_install_path)

        with open(conf, 'w') as f:
            f.write(yaml.dump(group_setting))

    elif type(conf) is dict:
        group_setting = conf
        group_setting.setdefault('path', []).append(service_install_path)

    return group_setting


if __name__ == '__main__':
    p = os.path.realpath(os.path.join(cur_dir, '../examples/micro_service/setting.yaml'))
    s_c = get_service_group(p)
    from pprint import pprint

    pprint(s_c)
