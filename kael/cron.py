#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@version:
@author:
@time: 2017/6/15
"""

import logging
from crontab import CronTab
import os
import click

COMMON_PREFIX = 'KaelCron_'


class Cron(object):
    cron = None
    jobs = {}  # keys are jobs name_id, used as comment in contab
    to_add_jobs = {}
    
    def __init__(self, prefix=COMMON_PREFIX):
        # this must use this load current user cron, otherwise will empty other cron jobs
        self.commet_pre_str = prefix
        self.cron = CronTab(user=True)
    
    def add(self, command='', time_str='', job_name=''):
        """添加任务至待保存区，没有真正添加"""
        if not job_name:
            return False
        if not job_name.startswith(self.commet_pre_str):
            job_name = self.commet_pre_str + job_name
        
        # 检查任务是否正常，不真正写入
        try:
            cron = CronTab(user=True)
            job = cron.new(command=command, comment=job_name)
            if job.setall(time_str):
                self.to_add_jobs.setdefault(job_name, []).append(dict(command=command, time_str=time_str))
                return True
            return False
        except Exception as e:
            logging.warn("Error in add job:%s" % e)
            return False
    
    def active_add_jobs(self):
        """激活所有添加的job，单纯的添加所有待添加job。不检查是否已存在job_name"""
        for job_name, jobs in self.to_add_jobs.iteritems():
            for c_t in jobs:
                job = self.cron.new(command=c_t['command'], comment=job_name)
                job.setall(c_t['time_str'])
        self.cron.write_to_user(user=True)
        self.to_add_jobs.clear()
        return True
    
    def del_job(self, job_name=None):
        try:
            if job_name:
                if not job_name.startswith(self.commet_pre_str):
                    job_name = self.commet_pre_str + job_name
                objs = self.cron.find_comment(job_name)
            else:
                objs = self.cron
            
            for obj in objs:
                self.cron.remove(obj)
            self.cron.write(user=True)
            logging.warn("[{0} {1}] succeed to remove job({2})".format(" Cron_Update", "del_job", job_name))
            return True
        except Exception as e:
            logging.warn("[{0} {1}] {2}".format(" Cron_Update", "del_job", e))
        return False
    
    def cron_jobs(self, job_name=None):
        """列出执行用户的定时任务"""
        res = {}
        if job_name:
            if not job_name.startswith(self.commet_pre_str):
                job_name = self.commet_pre_str + job_name
            jobs = self.cron.find_comment(job_name)
        else:
            jobs = self.cron
        for i, tmpjob in enumerate(jobs):
            # logging.warn("-------cron job{0}: {1}".format(i, tmpjob))
            time_str = ' '.join(map(str, tmpjob.slices))
            res.setdefault(tmpjob.comment, []).append(dict(command=tmpjob.command, time_str=time_str))
        return res
    
    def micro_service_add_modify_job(self, job_name=None, jobs=None):
        """
        微服务使用，没有job_name则新增，有job_name则删除旧job
        :param job_name: 名称
        :param jobs: 名称下的所有定时任务 [{'command':'', 'time_str':'' }]
        :return:
        """
        
        try:
            # logging.warn("Info: update_crontab.add_modify:%s,%s,%s"%(command, time_str, job_name))
            if not job_name:
                return False
            if not job_name.startswith(self.commet_pre_str):
                job_name = self.commet_pre_str + job_name
            jobs = jobs or {}
            
            # 删除已有
            self.del_job(job_name=job_name)
            
            # 添加新的
            for job in jobs:
                self.add(command=job['command'], time_str=job['time_str'], job_name=job_name)
            return self.active_add_jobs()
        except Exception as e:
            logging.warn("Error in update_crontab.add_modify:%s" % e)
        return False


def test():
    t = Cron()
    # === add
    print t.add(command='echo 1', time_str='* * * * *', job_name='test')
    print t.add(command='echo 2', time_str='* * * * *', job_name='test')
    print t.add(command='echo 3', time_str='* * * * *', job_name='test')
    print t.active_add_jobs()
    print
    # === del
    print t.del_job("test")
    # print t.del_job()
    
    # === micro_service_add_modify_job
    job_name = 'test-micro_service'
    jobs1 = [{'command': 'echo 1', 'time_str': '* * * * *'},
             {'command': 'echo 2', 'time_str': '* * * * *'},
             {'command': 'echo 3', 'time_str': '* * * * *'}
             ]
    print t.micro_service_add_modify_job(job_name=job_name, jobs=jobs1)
    
    jobs2 = [{'command': 'echo 11', 'time_str': '*/15 * * * *'},
             {'command': 'echo 21', 'time_str': '2 * * * *'},
             {'command': 'echo 31', 'time_str': '* * * * *'}
             ]
    print t.micro_service_add_modify_job(job_name=job_name, jobs=jobs2)
    
    print t.cron_jobs()


# region
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


def kael_crontab():
    cli()
# end region


if __name__ == "__main__":
    test()
