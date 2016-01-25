# -*- coding: utf-8 -*-
from django import forms

import xadmin
from xadmin.views.page import PageView,FormPage,GridPage
from xadmin.widgets import AjaxSearchWidget
from xadmin.layout import Fieldset, Main, Side, Row, FormHelper

class ImportTagsForm(forms.Form):
    product = forms.IntegerField(label=u'妆品标签', required=False, widget=AjaxSearchWidget('/auth/user/'))
    custom = forms.DateField(label=u'自定义标签', required=False, widget=AjaxSearchWidget('/auth/user/') )
    


class VtalkTags(FormPage):
    verbose_name = '话题标签'
    form = ImportTagsForm
    title = '话题标签管理'
    form_template= 'vtalk_tags_form.html'
    
#    form_layout = (
#                   Row('product', 'custom')
#                   )
    
    form_layout = (
                   Fieldset( 'Personal info',
                            Row('product', 'custom'),
                            css_class='unsort short_label no_title'
                             ),
                   )
    
    def get_context(self):
        context = super(VtalkTags, self).get_context()
        pa_list = [
                   {'param':'A1','descript':'B1','type':'C1'},
                   {'param':'A2','descript':'B2','type':'C2'},
                   {'param':'A3','descript':'B3','type':'C3'},
                   ]
        context.update({
            'pa_list': pa_list,
        })
        return context
    
    def save_forms(self):
        print '---------------',dir(self.request.POST)
        m_params = self.request.POST.getlist('param')
        m_descripts = self.request.POST.getlist('descript')
        m_types = self.request.POST.getlist('type')
        print 'ssssss',m_params,m_descripts,m_types
        pass
    
xadmin.site.register_page(VtalkTags)