# -*- coding: utf-8 -*-
"""
错误码使用规范:
http://10.16.66.8:9000/pages/viewpage.action?pageId=5248642
"""

OK = 10000


class BaseError(Exception):
    status = None
    description = None

    def __init__(self, description=None):
        if description is not None:
            self.description = description

    def __str__(self):
        return '%d: %s' % (self.status, self.description)

    def __repr__(self):
        return '<%s \'%s\'>' % (self.__class__.__name__, self)


class UnknownError(BaseError):
    """ Uncatch error. """
    status = 10999
    description = 'Unknown Error'


class AuthError(BaseError):
    status = 10101
    description = "Auth Failed"


class InvalidTokenError(BaseError):
    status = 10102
    description = "Invalid Token"


class ArgumentError(BaseError):
    """ Argument error. """
    status = 10201
    description = 'Argument Error'


class MissArgumentError(ArgumentError):
    """ Miss argument error. """
    status = 10202
    description = 'Miss Argument Error'


class NoFoundObjError(ArgumentError):
    """ Miss argument error. """
    status = 10203
    description = 'Not Found Obj Error'


class ObjExistError(ArgumentError):
    """ Miss argument error. """
    status = 10204
    description = 'Obj Exist Error'


class InternalError(BaseError):
    """ System error. """
    status = 10301
    description = 'Internal Error'


class TimeoutError(InternalError):
    """ Raised when the process time beyond the limitation. """
    status = 10302
    description = 'Process Timeout'


class UnsupportedError(ArgumentError):
    """ Raised when feature not support. """
    status = 10303
    description = 'Feature Unsupported'


class WebProxyError(BaseError):
    """ Raised when bad gateway of webproxy url . """
    status = 10304
    description = 'Webproxy URL, Error'
