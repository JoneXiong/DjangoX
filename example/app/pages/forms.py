# coding=utf-8

from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.utils.encoding import force_text

import xadmin
from xadmin.widgets import AjaxSearchWidget
from xadmin import dutils

from . ext_form_fields import MyField
from .ext_widgets import TextInputCounter



class TestForm(forms.Form):
    u'''
    自定义Form
    '''
    members = MyField(label=u'自定义字段', max_length=1024, widget=forms.Textarea, required=True, help_text=u'以"x"开头')

    #members = MembersField(label=u'自定义字段', max_length=1024, widget=forms.Textarea, required=True, help_text=u'用逗号分隔')

    account = forms.IntegerField(label=u'Integer字段', required=True)
    charge_time = forms.DateField(label=u'Date字段', required=True, widget=xadmin.widgets.DateWidget)
    amount = forms.DecimalField(label=u'Decimal字段', required=True, max_digits=10, decimal_places=2)
    title = forms.CharField(label=u'Char字段', required=True, max_length=100)
    note = forms.CharField(label=u'自定义widget的Char字段', required=False, widget=TextInputCounter())

    select1 = forms.IntegerField(label=u'Choices选择字段', required=False, widget=xadmin.widgets.SelectWidget(choices=((1,'A'),(2,'B'),(3,'C'))) )
    select2 = forms.IntegerField(label=u'Ajax选择字段', required=False, widget=AjaxSearchWidget('/auth/user/') )

    def clean_note(self):
        m_note = self.cleaned_data.get('note')
        if m_note=='1':
            raise forms.ValidationError('备注不能为1')
