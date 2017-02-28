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

if django.VERSION[1] >= 9:
    from django.db.models.options import Options
    def get_all_related_objects(self):
        return [
                f for f in self.get_fields()
                if (f.one_to_many or f.one_to_one)
                and f.auto_created and not f.concrete
        ]
    Options.get_all_related_objects = get_all_related_objects
    def get_all_related_many_to_many_objects(self):
        return [
                f for f in self.get_fields(include_hidden=True)
                if f.many_to_many and f.auto_created
        ]
    Options.get_all_related_many_to_many_objects = get_all_related_many_to_many_objects
    def get_field_by_name(self,name):
        return [self.get_field(name)]
    Options.get_field_by_name = get_field_by_name

from .initialize import autodiscover
