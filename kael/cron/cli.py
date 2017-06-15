#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@version:
@author:
@time: 2017/6/15
"""
import os

import click


@click.group()
def cli():
    pass


def _check_task_is_py(command):
    command = command.strip()
    head = command.split(' ')[0]
    if 'py' == head.split('.')[-1]:
        return True
    return False


@cli.command('run', short_help='Run task of cron with env.')
@click.option('-c', help='Command string')
@click.option('-d', help='Absolute directory of task')
@click.option('-p', help='Python interpreter location')
def run(c, d, p):
    if not d:
        raise Exception('No absolute directory of task, use -d')
    os.chdir(d)
    
    python_env = p if p else 'python'
    
    if not c:
        raise Exception('No command string')
    if _check_task_is_py(c):
        os.system('{} {}'.format(python_env, c))
    else:
        os.system(c)


def main():
    cli()


if __name__ == '__main__':
    main()
