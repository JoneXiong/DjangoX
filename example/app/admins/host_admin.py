# coding=utf-8

import xadmin
from xadmin import layout

from app import models


class MaintainInline(object):
    model = models.MaintainLog
    extra = 1
    style = 'accordion'

class HostAdmin(object):
    
    def open_web(self, instance):
        return "<a href='http://%s' target='_blank'>Open</a>" % instance.ip
    open_web.short_description = "Acts"
    open_web.allow_tags = True
    open_web.is_column = True

    list_display = ('name', 'idc', 'guarantee_date', 'service_type', 'status', 'open_web', 'description')
    list_display_links = ('name',)
    

    raw_id_fields = ('idc',)
    style_fields = {'system': "radio-inline"}

    search_fields = ['name', 'ip', 'description']
    list_filter = ['id','idc', 'guarantee_date', 'status', 'brand', 'model',
                   'cpu', 'core_num', 'hard_disk', 'memory', ('service_type',xadmin.filters.MultiSelectFieldListFilter)]
    
    #list_quick_filter = ['service_type',{'field':'idc__name','limit':10}]
    list_bookmarks = [{'title': "Need Guarantee", 'query': {'status__exact': 2}, 'order': ('-guarantee_date',), 'cols': ('brand', 'guarantee_date', 'service_type')}]

    show_detail_fields = ('idc',)
    list_editable = (
        'name', 'idc', 'guarantee_date', 'service_type', 'description')
    save_as = True

    aggregate_fields = {"guarantee_date": "min"}
    grid_layouts = ('table', 'thumbnails')

    form_layout = (
        layout.Main(
            layout.TabHolder(
                layout.Tab('Comm Fields',
                    layout.Fieldset('Company data',
                             'name', 'idc',
                             description="some comm fields, required"
                             ),
#                    Inline(MaintainLog),
                    ),
                layout.Tab('Extend Fields',
                    layout.Fieldset('Contact details',
                             'service_type',
                             layout.Row('brand', 'model'),
                             layout.Row('cpu', 'core_num'),
                             layout.Row(layout.AppendedText(
                                 'hard_disk', 'G'), layout.AppendedText('memory', "G")),
                             'guarantee_date'
                             ),
                    ),
            ),
        ),
        layout.Side(
            layout.Fieldset('Status data',
                     'status', 'ssh_port', 'ip'
                     ),
        )
    )
    inlines = [MaintainInline]
    reversion_enable = True
#     relfield_style = 'fk-ajax'
    
    data_charts = {
        "host_service_type_counts": {'title': u"Host service type count", "x-field": "service_type", "y-field": ("service_type",), 
                              "option": {
                                         "series": {"bars": {"align": "center", "barWidth": 0.8,'show':True}}, 
                                         "xaxis": {"aggregate": "count", "mode": "categories"},
                                         },
                              },
    }
    model_icon = 'fa fa-laptop'
    
xadmin.site.register(models.Host, HostAdmin)