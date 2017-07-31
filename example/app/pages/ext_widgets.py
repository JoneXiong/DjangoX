# coding=utf-8

from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.utils.encoding import force_text

import xadmin
from xadmin.widgets import AjaxSearchWidget
from xadmin import dutils


# 自定义widget 
class TextInputCounter(forms.TextInput):
    """
    显示已经输入多少字符的widget
    """

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        self.attrs.update({'class': '%s textinput' % self.attrs.get('class', '')})
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '':
            final_attrs['value'] = force_text(self._format_value(value))
        templ = """
        <input{0} onkeyup='javascript:count(this);' />
        <span class='label label-default'>已输入<span class='counter'>%s</span>个字</span>
        """ % len(value)
        script = """
        <script>
            function count(field){
                var counter_label = $(field).next('span').children('span');
                counter_label.html($(field).val().length);
            }
        </script>
        """
        html = format_html(templ, dutils.flatatt(final_attrs))
        return '%s%s' % (html, script)
 

