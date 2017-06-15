#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@version:
@author:
@time: 2017/6/15
"""

import logging
from crontab import CronTab

COMMON_PREFIX = 'KaelCron_'

__all__ = ['Cron']


class Cron(object):
    cron = None
    jobs = {}  # keys are jobs name_id, used as comment in contab
    to_add_jobs = {}
    
    def __init__(self, prefix=COMMON_PREFIX):
        # this must use this load current user crontab, otherwise will empty other cron jobs
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
    
    def del_job(self, job_name):
        try:
            if not job_name:
                return False
            if not job_name.startswith(self.commet_pre_str):
                job_name = self.commet_pre_str + job_name
            
            objs = self.cron.find_comment(job_name)
            for obj in objs:
                self.cron.remove(obj)
            self.cron.write(user=True)
            logging.warn("[{0} {1}] succeed to remove job({2})".format(" Cron_Update", "del_job", job_name))
            return True
        except Exception as e:
            logging.warn("[{0} {1}] {2}".format(" Cron_Update", "del_job", e))
        return False
    
    def cron_jobs(self, job_name=None):
        # todo
        res = {}
        for i, tmpjob in enumerate(self.cron):
            logging.warn("-------crontab job{0}: {1}".format(i, tmpjob))
            res[tmpjob.comment] = tmpjob
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
    
    # === micro_service_add_modify_job
    job_name = 'test-micro_service'
    jobs1 = [{'command': 'echo 1', 'time_str': '* * * * *'},
             {'command': 'echo 2', 'time_str': '* * * * *'},
             {'command': 'echo 3', 'time_str': '* * * * *'}
             ]
    print t.micro_service_add_modify_job(job_name=job_name, jobs=jobs1)
    
    jobs2 = [{'command': 'echo 11', 'time_str': '* * * * *'},
             {'command': 'echo 21', 'time_str': '* * * * *'},
             {'command': 'echo 31', 'time_str': '* * * * *'}
             ]
    print t.micro_service_add_modify_job(job_name=job_name, jobs=jobs2)


if __name__ == "__main__":
    test()
