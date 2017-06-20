# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/7
from jsonschema._format import _checks_drafts, _draft_checkers, FormatChecker
import datetime
import re
from jsonschema.compat import str_types


@_checks_drafts("timestamp", raises=ValueError)
def timestamp(instance):
    if instance:
        return datetime.datetime.strptime(instance, "%Y-%m-%d %H:%M:%S")
    else:
        return True


@_checks_drafts("md5", raises=ValueError)
def is_md5(instance):
    if not isinstance(instance, str_types):
        return True
    return re.match('[a-fA-F0-9]{32}', instance)


formatchecker = FormatChecker(_draft_checkers["draft4"])
