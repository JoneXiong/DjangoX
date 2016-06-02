# -*- coding: utf-8 -*-

VERSION = [0,5,0]

ROOT_PATH_NAME = ''
EXPORT_MAX = 100000
DEFAULT_RELFIELD_STYLE = {
                          'fk': '',
                          'm2m': ''
                          }

verbose_name = u'系统'

menus = (
         ('auth_group', u'权限',  'auth_icon'),
         )

from xadmin.sites import site
from .initialize import autodiscover