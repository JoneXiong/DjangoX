# coding=utf-8

import xadmin
from xadmin.views.model_page import ModelAdmin
from xadmin.plugins.batch import BatchChangeAction

from app import models


class IDCAdmin(ModelAdmin):
    list_display = ('name', 'description', 'create_time')
    list_display_links = ('name',)
    wizard_form_list = [
        ('First\'s Form', ('name', 'description')),
        ('Second Form', ('contact', 'telphone', 'address')),
        ('Thread Form', ('customer_id',))
    ]

    search_fields = ['name']
    #relfield_style = 'fk-ajax'
    reversion_enable = True

    actions = [BatchChangeAction, ]
    batch_fields = ['contact', 'name']
    list_export = ['xlsx', 'xls', 'csv', 'xml', 'json']
    model_icon = 'fa fa-cloud'

xadmin.site.register(models.IDC, IDCAdmin)