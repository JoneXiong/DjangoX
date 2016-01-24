# coding=utf-8

import functools
from inspect import getargspec

class IncorrectPluginArg(Exception):
    """ 当插件的方法参数错误时抛出该异常 """
    pass


def filter_chain(filters, token, func, *args, **kwargs):
    if token == -1:
        return func()
    else:
        def _inner_method():    # fm 当前函数    func 前函数
            fm = filters[token]
            fargs = getargspec(fm)[0]
            if len(fargs) == 1:
                # 只有 self 一个参数，如果前一函数执行返回不为空则会抛出异常
                result = func()
                if result is None:
                    return fm()
                else:
                    raise IncorrectPluginArg(u'Plugin filter method need a arg to receive parent method result.')
            else:
                # 如果第一个参数为 __ ，则将前函数作为参数传到当前函数执行（通过 __() 执行）， 否则将前函数的执行结果传过去
                return fm(func if fargs[1] == '__' else func(), *args, **kwargs)
        return filter_chain(filters, token - 1, _inner_method, *args, **kwargs)


def filter_hook(func):
    tag = func.__name__
    func.__doc__ = "``filter_hook``\n\n" + (func.__doc__ or "")

    @functools.wraps(func)
    def method(self, *args, **kwargs):

        def _inner_method():
            return func(self, *args, **kwargs)

        if self.plugins:
            filters = [ ( getattr( getattr(p, tag), 'priority', 10 ), getattr(p, tag) ) for p in self.plugins if callable(getattr(p, tag, None)) ]
            # 按照 priority 属性排序
            filters = [f for p, f in sorted(filters, key=lambda x:x[0])]
            return filter_chain(filters, len(filters) - 1, _inner_method, *args, **kwargs)
        else:
            return _inner_method()
    return method