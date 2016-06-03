# coding=utf-8

import xadmin
from xadmin.views.page import GridPage
from xadmin.views.list import ResultRow
from xadmin.views.base import filter_hook

from form_actions import FormAction1



from xadmin.filters import BaseFilter
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _


class ChoicesBaseFilter(BaseFilter):
    
    title = None
    parameter_name = None

    def __init__(self, request, params, model, admin_view):
        super(ChoicesBaseFilter, self).__init__(request, params, model, admin_view)
        if self.parameter_name is None:
            raise ImproperlyConfigured(
                "The list filter '%s' does not specify "
                "a 'parameter_name'." % self.__class__.__name__)
        lookup_choices = self.lookups(request, admin_view)
        if lookup_choices is None:
            lookup_choices = ()
        self.lookup_choices = list(lookup_choices)
        if self.parameter_name in params:
            value = params.pop(self.parameter_name)
            self.used_params[self.parameter_name] = value
        
       
    def lookups(self, request, admin_view):
        raise NotImplementedError
        
    def choices(self):
        yield {
            'selected': self.value() is None,
            'query_string': self.query_string({}, ['_p_'+self.parameter_name]),
            'display': _('All'),
        }
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': self.query_string({'_p_'+self.parameter_name: lookup,}, []),
                'display': title,
            }
    
    def get_context(self):
        context = super(ChoicesBaseFilter, self).get_context()
        context['choices'] = list(self.choices())
        return context
    
    def has_output(self):
        return len(self.lookup_choices) > 0

    def value(self):
        return self.used_params.get(self.parameter_name, None)
    
    def do_filte(self, queryset):
        raise NotImplementedError


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