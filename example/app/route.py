# coding=utf-8
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django import forms
#from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.forms.formsets import formset_factory

import xadmin
from xadmin import site
from xadmin.views.base import SiteView, BaseView
from xadmin.views.form import FormAdminView

from xadmin.views.page import PageView,FormPage,GridPage
from xadmin.views.list import ResultRow, ResultItem

from test_form import TestForm





class TestPage(PageView):
    template = 'xadmin/views/page.html'
    site_title = 'Test Page2'
    
    def get_context(self):
        context = super(TestPage, self).get_context()
        context.update({
                        'content': self.get_content() or '',
                        'formset': formset_factory(TestForm, extra=2)
                        })
        return context
    
    def get_media(self):
        media = self.vendor('xadmin.plugin.quick-form.js', 'xadmin.form.css')
        return media
    
    def get_content(self):
        return mark_safe('<a data-refresh-url="/page/testpage/" href="/test_form" class="ajaxform-handler" title="测试AjaxForm">GO</a>') 
site.register_page(TestPage)


class MembersField(forms.CharField):

    def to_python(self, value):
        ms = []
        for n in re.split('[,\t\n]',value):
            n = n.replace('\n','').replace('\r','').replace('\t','').replace(',','')
            try:
                ms.append(Member.objects.get(number=n))
            except Exception:
                ms.append(n)
        return ms

    def validate(self, value):
        super(MembersField, self).validate(value)
        miss = []
        for m in value:
            if type(m) is not Member:
                miss.append(m)
        if len(miss):
            raise ValidationError(','.join(miss) + ' 未找到对应的用户', code='miss_number')






class TestFormPage(FormPage):
    form = TestForm
    title = 'Test Form Page'
    
    def get_context(self):
        context = super(TestFormPage, self).get_context()
        context.update({
                        'content': self.get_content() or '',
                        'formset': formset_factory(TestForm, extra=2)
                        })
        return context
    
site.register_page(TestFormPage)


class TestGridPage(GridPage):
    verbose_name = '测试 自定义列表页'
    head = [('pin',u'工号'),('EName',u'姓名'),('Card',u'卡号')]
    

#{
#'num_sorted_fields': 0,
#'cells': [{'label':'字段1'},{'label':'字段1'},{'label':'字段1'}]
#}


# [
#                    {
#                        'cells': [{'label':mark_safe('<input class="action-select" name="_selected_action" type="checkbox" value="32">')},{'label':1},{'label':2},{'label':3}],
#                         'is_display_first': False
#                    },
#                     {
#                        'cells': [{'label':mark_safe('<input class="action-select" name="_selected_action" type="checkbox" value="32">')},{'label':1},{'label':2},{'label':3}],
#                         'is_display_first': False
#                    },
#                     {
#                        'cells': [{'label':mark_safe('<input class="action-select" name="_selected_action" type="checkbox" value="32">')},{'label':1},{'label':2},{'label':3}],
#                         'is_display_first': False
#                    },
#                     {
#                        'cells': [{'label':mark_safe('<input class="action-select" name="_selected_action" type="checkbox" value="32">')},{'label':1},{'label':2},{'label':3}],
#                         'is_display_first': False
#                    },
#                     {
#                        'cells': [{'label':mark_safe('<input class="action-select" name="_selected_action" type="checkbox" value="32">')},{'label':1},{'label':2},{'label':3}],
#                         'is_display_first': False
#                    }
#                ],



    
    def get_data(self):
        row = ResultRow()
        item1 = ResultItem("pin", row)
        item1.text = 1
        row.cells.append(item1)
        
        item2 = ResultItem("EName", row)
        item2.text = 2
        row.cells.append(item2)
        
        item3 = ResultItem("Card", row)
        item3.text = 2
        row.cells.append(item3)
        
        return [row,row,row,row,row]
    
site.register_page(TestGridPage)