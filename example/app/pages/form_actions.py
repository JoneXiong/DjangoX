# coding=utf-8

from django import forms

import xadmin
from xadmin.views.page import FormPage, FormAction
from xadmin.core.form_fields import MultiSelectFormField


class MyForm(forms.Form):
    account = forms.IntegerField(label=u'选择账户', required=True)
    charge_time = forms.DateField(label=u'支付时间', required=True, widget=xadmin.widgets.DateWidget)
    test = forms.MultipleChoiceField(choices=[('a','a'),('b','b')],help_text='按住Ctrl键多选')
    test2 = MultiSelectFormField(choices=[('a','aaaa'),('b','bbbb'),('c','cccc'),('d','dddd')])
    
    
class FormAction1(FormAction):
    app_label = 'app'
    menu_group = 'test_group'
    verbose_name = 'FormAction1'
    form = MyForm
    title = '标签导入'
    
    def save_forms(self):
        for e in self.get_id_list():
            print '999999999999999',e
#             import json
#             print json.loads(e)['id']
    
xadmin.site.register_page(FormAction1)