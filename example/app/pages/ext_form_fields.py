# coding=utf-8
import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html

import xadmin
from xadmin.widgets import AjaxSearchWidget
from xadmin import dutils


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


class MyField(forms.CharField):
    u'''
    自定义Field
    '''
    def to_python(self, value):
        return '_' + value

    def validate(self, value):
        super(MyField, self).validate(value)
        if not value.startswith('_x'):
            raise ValidationError('必须以"x"开头', code='miss_number')
