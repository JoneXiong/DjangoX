# -*- coding: utf-8 -*-

VERSION = [0,1,0]

ROOT_PATH_NAME = ''
EXPORT_MAX = 100000
DEFAULT_RELFIELD_STYLE = {
                          'fk': '',
                          'm2m': ''
                          }

verbose_name = u'系统'

menus = (
         ('auth_group', u'权限',  'fa-user-plus'),
         )

# django patch
import django
if django.VERSION[1] > 7:
    from django.db.models.options import Options
    @property
    def monkeypatch__options__model_name(self):
        return self.model_name
    Options.module_name = monkeypatch__options__model_name

from .initialize import autodiscover
