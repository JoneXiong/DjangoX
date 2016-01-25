# coding=utf-8

from django import forms

import xadmin
from xadmin.views.page import FormPage, FormAction


class ImportTagsForm(forms.Form):
    account = forms.IntegerField(label=u'选择账户', required=True)
    charge_time = forms.DateField(label=u'支付时间', required=True, widget=xadmin.widgets.DateWidget)


class ImportTags(FormPage):
    app_label = 'app'
    menu_group = 'test_group'
    verbose_name = '标签导入'
    form = ImportTagsForm
    title = '标签导入'
xadmin.site.register_page(ImportTags)


class ImportTags2(FormAction):
    app_label = 'app'
    menu_group = 'test_group'
    verbose_name = '标签导入'
    form = ImportTagsForm
    title = '标签导入'
    
    def save_forms(self):
        for e in self.get_id_list():
            print e
            import json
            print json.loads(e)['id']
    
xadmin.site.register_page(ImportTags2)