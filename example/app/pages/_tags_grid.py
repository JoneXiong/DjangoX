# -*- coding: utf-8 -*-
from django import forms

import xadmin
from xadmin.views.page import PageView,FormPage,GridPage
from xadmin.views.list import ResultRow, ResultItem

class ImportTagsForm(forms.Form):
    account = forms.IntegerField(label=u'选择账户', required=True)
    charge_time = forms.DateField(label=u'支付时间', required=True, widget=xadmin.widgets.DateWidget)
    
    
class ImportTags(FormPage):
    form = ImportTagsForm
    verbose_name = '导入标签'
    title = '标签导入'

#xadmin.site.register_page(ImportTags)

class Tags(GridPage):
    
    verbose_name = '标签库'
    head = [ ('id',u'ID'), ('tag',u'标签'), ('alias',u'关联标签'), ('vtalk_c',u'话题数量') ]
    

#    def get_data(self):
#        row = ResultRow()
#        row.add_cell('id', 1)
#        row.add_cell('tag', 2)
#        row.add_cell('alias', 3)
#        row.add_cell('vtalk_c', 4)
#        return [row,row,row,row,row]

    def get_nav_btns(self):
        return [ ImportTags.render_btn(self.get_url()) ]
    
#xadmin.site.register_page(Tags)