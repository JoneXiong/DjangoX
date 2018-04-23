# coding=utf-8

from django import forms

import xadmin
from xadmin.views.page import FormPage, FormAction
from xadmin.core.form_fields import MultiSelectFormField


class MyForm(forms.Form):
    account = forms.IntegerField(label=u'账户', required=True)
    charge_time = forms.DateField(label=u'支付时间', required=True, widget=xadmin.widgets.DateWidget)
    test = forms.MultipleChoiceField(choices=[('a','a'),('b','b')],help_text='按住Ctrl键多选')


class FormPage1(FormPage):
    app_label = 'app'
    menu_group = 'test_group'
    verbose_name = 'FormPage1'
    form = MyForm

    def get_nav_btns(self):
        return [
            '<a href="#" class="btn btn-primary"><i class="fa fa-refresh"></i> 链接一</a>',
            '<a href="#" class="btn btn-success"><i class="fa fa-filter"></i> 链接二</a>',
            '<a href="#" class="btn btn-info"><i class="fa fa-plus"></i> 链接三</a>',
        ]

    def save_forms(self):
        print(self.form_obj.cleaned_data)

xadmin.site.register_page(FormPage1)


