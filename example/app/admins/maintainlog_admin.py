# coding=utf-8

import xadmin
from xadmin import layout

from app import models

class MaintainLogAdmin(object):
    list_display = (
        'host', 'maintain_type', 'hard_type', 'time', 'operator', 'note')
#     list_display_links = ('host',)
# 
#     list_filter = ['host', 'maintain_type', 'hard_type', 'time', 'operator']
    search_fields = ['note']

    form_layout = (
        layout.Col("col2",
            layout.Fieldset('Record data',
                     'time', 'note',
                     css_class='unsort short_label no_title'
                     ),
            span=9, horizontal=True
            ),
        layout.Col("col1",
            layout.Fieldset('Comm data',
                     'host', 'maintain_type'
                     ),
            layout.Fieldset('Maintain details',
                     'hard_type', 'operator'
                     ),
            span=3
            )
    )
    reversion_enable = True
    log = True
    
xadmin.site.register(models.MaintainLog, MaintainLogAdmin)