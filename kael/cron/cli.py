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
def run(c, d):
    """Run task of cron with env."""
    if not d:
        raise click.BadParameter('No absolute directory of task, use -d')
    os.chdir(d)
    
    if not c:
        raise click.BadParameter('No command string, use -c')
    if _check_task_is_py(c):
        os.system('python {}'.format(c))
    else:
        os.system(c)


def main():
    cli()


if __name__ == '__main__':
    main()
