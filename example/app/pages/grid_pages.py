# coding=utf-8
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _

import xadmin
from xadmin.views.page import GridPage
from xadmin.views.list import ResultRow
from xadmin.views.base import filter_hook
from xadmin.filters import ChoicesBaseFilter

from form_actions import FormAction1


class GridListFilter1(ChoicesBaseFilter):

    title = '筛选'
    parameter_name = 'param1'

    def lookups(self, request, admin_view):
        return (
                ('1', '选项一'),
                ('2', '选项二'),
                ('3', '选项三'),
               )

    def do_filte(self, queryset):
        m_value = self.value()
        if not m_value:
            return queryset
        if m_value == '1':
            return queryset
        elif m_value == '2':
            return queryset
        elif m_value == '3':
            return queryset
        return queryset


class GridPage1(GridPage):
    app_label = 'app'
    menu_group = 'test_group'
    verbose_name = 'GridPage1'
    head = [ ('id',u'ID'), ('tag',u'标签'), ('alias',u'关联标签'), ('vtalk_c',u'话题数量') ]

    search_fields = ('tag',)
    #list_filter = ['tag', ('alias',xadmin.filters.BooleanFieldListFilter)]
    list_filter = [GridListFilter1, ]

    form_actions = [FormAction1]
    val_list = ['id', 'tag']

    @filter_hook
    def get_list_queryset(self):
        data = [
                {'id':1111, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':2, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':3, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':4, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':5, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':1, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':2, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':3, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':4, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':5, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':1, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':2, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':3, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':4, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':5, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':1, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':2, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':3, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':4, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':5, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':1, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':2, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':3, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':4, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':5, 'tag':2, 'alias':3, 'vtalk_c':4},
                ]
        from xadmin.db.query import Collection
        return Collection(data)

xadmin.site.register_page(GridPage1)
