# coding=utf-8

import xadmin

from app import models

class AAdmin(object):
    list_display = ['name', 'b', 'sex', 'ename']
    pass
xadmin.site.register(models.A, AAdmin)