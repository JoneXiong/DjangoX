# coding=utf-8

import xadmin

from app import models

class AAdmin(object):
    pass
xadmin.site.register(models.A, AAdmin)