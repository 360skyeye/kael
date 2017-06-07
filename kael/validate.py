# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/7
from jsonschema._format import _checks_drafts, _draft_checkers, FormatChecker
import datetime


@_checks_drafts("timestamp", raises=ValueError)
def timestamp(instance):
    if instance:
        return datetime.datetime.strptime(instance, "%Y-%m-%d %H:%M:%S")
    else:
        return True


formatchecker = FormatChecker(_draft_checkers["draft4"])
