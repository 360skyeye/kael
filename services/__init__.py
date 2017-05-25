#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@version: 
@author:
@time: 2017/5/25 15:53
"""
import logging
import os
import yaml

__all__ = ['Services']
Services = {}

cur_dir = os.path.dirname(os.path.abspath(__file__))
for pkg in os.listdir(cur_dir):
    try:
        if pkg.split('.')[-1].lower() not in ('py', 'pyc', 'md'):

            # 1 export setting.yaml into Services
            setting_file = os.path.join(cur_dir, pkg, 'setting.yaml')
            with open(setting_file) as f:
                s = yaml.load(f.read())
                if s['service_name'] in Services:
                    logging.error('Registering from {}'.format(setting_file))
                    raise Exception('Service Name Already Existed: {0}'.format(s['service_name']))
                else:
                    Services[s['service_name']] = s

            # 2 export run function into Services
            module = __import__('services.{0}.__init__'.format(pkg), fromlist='dummy')
            run = getattr(module, 'run')
            Services[s['service_name']]['function'] = run
    except Exception as e:
        logging.exception(e)

