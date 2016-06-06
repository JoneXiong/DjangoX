# coding=utf-8

from django import forms

import xadmin
from xadmin.views.page import FormPage, FormAction
from xadmin.core.form_fields import MultiSelectFormField


class MyForm(forms.Form):
    account = forms.IntegerField(label=u'选择账户', required=True)
    charge_time = forms.DateField(label=u'支付时间', required=True, widget=xadmin.widgets.DateWidget)
    test = forms.MultipleChoiceField(choices=[('a','a'),('b','b')],help_text='按住Ctrl键多选')
    #test2 = MultiSelectFormField(choices=[('a','aaaa'),('b','bbbb'),('c','cccc'),('d','dddd')])


class FormPage1(FormPage):
    app_label = 'app'
    menu_group = 'test_group'
    verbose_name = 'FormPage1'
    form = MyForm
    
    def get_nav_btns(self):
        return [
                 '<a href="/xadmin/page/tags/?_q_=id_desc" class="btn btn-primary"><i class="fa fa-refresh"></i> 查看最新标签</a>',
                 '<a href="/xadmin/page/tags/?_q_=vtalk_c_50" class="btn btn-primary"><i class="fa fa-filter"></i> 精华话题大于50</a>',
                 '<a href="/xadmin/page/tags/?_q_=vtalk_c_100" class="btn btn-primary"><i class="fa fa-filter"></i> 精华话题大于100</a>',
                 '<a href="/xadmin/page/addtag/?_redirect=/xadmin/page/tags/" class="btn btn-primary"><i class="fa fa-plus"></i> 新增 标签</a>',
               ]
        
    def save_forms(self):
        print self.form_obj.cleaned_data
    
xadmin.site.register_page(FormPage1)


