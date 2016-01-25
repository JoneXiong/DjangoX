# -*- coding: utf-8 -*-

from django.http import HttpResponse, HttpResponseRedirect
import xadmin
from xadmin import views
from models import IDC, Host, MaintainLog, HostGroup, AccessRecord#, MyModel, MyModel2
from xadmin.layout import Main, TabHolder, Tab, Fieldset, Row, Col, AppendedText, Side
from xadmin.plugins.inline import Inline
from xadmin.plugins.batch import BatchChangeAction
from xadmin.plugins.actions import BaseActionView


xadmin.site.site_title = 'My Title'
xadmin.site.site_footer = 'My Footer'

class MainDashboard(object):
    widgets = [
        [
            {"type": "html", "title": "Test Widget", "content": "<h3> Welcome to MeiLa! </h3><p>Join us: <br/>Email : jone@meilapp.com</p>"},
            {"type": "chart", "model": "app.accessrecord", 'chart': 'user_count', 'params': {'_p_date__gte': '2013-01-08', 'p': 1, '_p_date__lt': '2013-01-29'}},
            {"type": "list", "model": "app.host", 'params': {'o':'-guarantee_date'}},
        ],
        [
            {"type": "qbutton", "title": "Quick Start", "btns": [{'model': Host}, {'model':IDC}, {'title': "MeiLa", 'url': "http://www.meilapp.com/"}]},
            {"type": "addform", "model": MaintainLog},
        ]
    ]
xadmin.site.register(views.website.IndexView, MainDashboard)


class BaseSetting(object):
    enable_themes = True
    use_bootswatch = True
xadmin.site.register(views.BaseAdminView, BaseSetting)


class GlobalSetting(object):
    
    global_search_models = [Host, IDC]
    global_models_icon = {
        Host: 'fa fa-laptop', IDC: 'fa fa-cloud'
    }
    menu_style = 'default'#'accordion'
    
    def get_site_menu(self):
        return [
                    {'title': u'内容管理', 'menus': [
                        {'title': u'游戏资料', 'perm':'auth.test_baidu', 'icon': 'fa fa-cloud', 'url': 'http://www.baidu.com/'},
                        {'title': u'网站文章', 'icon': 'fa fa-cloud', 'url': 'http://www.weibo.com/'},
                    ]}
                ]
    
xadmin.site.register(views.CommAdminView, GlobalSetting)


class MaintainInline(object):
    model = MaintainLog
    extra = 1
    style = 'accordion'

from xadmin.views.model_page import ModelAdmin
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
    batch_fields = ('contact', 'create_time')
    list_export = ['xlsx', 'xls', 'csv', 'xml', 'json']


class HostAdmin(object):
    def open_web(self, instance):
        return "<a href='http://%s' target='_blank'>Open</a>" % instance.ip
    open_web.short_description = "Acts"
    open_web.allow_tags = True
    open_web.is_column = True

    list_display = ('name', 'idc', 'guarantee_date', 'service_type',
                    'status', 'open_web', 'description')
    list_display_links = ('name',)
    

    raw_id_fields = ('idc',)
    style_fields = {'system': "radio-inline"}

    search_fields = ['name', 'ip', 'description']
    list_filter = ['id','idc', 'guarantee_date', 'status', 'brand', 'model',
                   'cpu', 'core_num', 'hard_disk', 'memory', ('service_type',xadmin.filters.MultiSelectFieldListFilter)]
    
    list_quick_filter = ['service_type',{'field':'idc__name','limit':10}]
    list_bookmarks = [{'title': "Need Guarantee", 'query': {'status__exact': 2}, 'order': ('-guarantee_date',), 'cols': ('brand', 'guarantee_date', 'service_type')}]

    show_detail_fields = ('idc',)
    list_editable = (
        'name', 'idc', 'guarantee_date', 'service_type', 'description')
    save_as = True

    aggregate_fields = {"guarantee_date": "min"}
    grid_layouts = ('table', 'thumbnails')

    form_layout = (
        Main(
            TabHolder(
                Tab('Comm Fields',
                    Fieldset('Company data',
                             'name', 'idc',
                             description="some comm fields, required"
                             ),
#                    Inline(MaintainLog),
                    ),
                Tab('Extend Fields',
                    Fieldset('Contact details',
                             'service_type',
                             Row('brand', 'model'),
                             Row('cpu', 'core_num'),
                             Row(AppendedText(
                                 'hard_disk', 'G'), AppendedText('memory', "G")),
                             'guarantee_date'
                             ),
                    ),
            ),
        ),
        Side(
            Fieldset('Status data',
                     'status', 'ssh_port', 'ip'
                     ),
        )
    )
#     inlines = [MaintainInline]
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
    
class MyAction(BaseActionView):

    # 这里需要填写三个属性
    action_name = "my_action_test"    #  Action 的唯一标示
    description = u'撤销' # 描述, 出现在 Action 菜单中, 可以使用 ``%(verbose_name_plural)s`` 代替 Model 的名字.

    model_perm = 'app.can_my_action_test'    # 该 Action 所需权限

    # 而后实现 do_action 方法
    def do_action(self, queryset):
        # queryset 是包含了已经选择的数据的 queryset
        for obj in queryset:
            print 'do action for ',obj,type(obj)
        # 返回 HttpResponse
        self.msg('no', 'error')
#         return HttpResponse('ok')    
    
class HostGroupAdd(views.CreateAdminView):
    
    def get_response(self):
        return self.render_text('ok')
#         return HttpResponse('ok')
    
class HostGroupAdmin(object):
    list_display = ('name', 'description')
    list_display_links = ('name', 'description')
    list_display_links_details = True
    list_per_page = 5
    list_editable = ('name','description')

    search_fields = ['name']
    style_fields = {'hosts': 'checkbox-inline'}
    
    view_changelist = None
    view_add = HostGroupAdd
    view_delete = None
    view_detail = None
    view_dashboard = None
    actions = [MyAction, ]


class MaintainLogAdmin(object):
    list_display = (
        'host', 'maintain_type', 'hard_type', 'time', 'operator', 'note')
    list_display_links = ('host',)

    list_filter = ['host', 'maintain_type', 'hard_type', 'time', 'operator']
    search_fields = ['note']

    form_layout = (
        Col("col2",
            Fieldset('Record data',
                     'time', 'note',
                     css_class='unsort short_label no_title'
                     ),
            span=9, horizontal=True
            ),
        Col("col1",
            Fieldset('Comm data',
                     'host', 'maintain_type'
                     ),
            Fieldset('Maintain details',
                     'hard_type', 'operator'
                     ),
            span=3
            )
    )
    reversion_enable = True


class AccessRecordAdmin(object):
    def avg_count(self, instance):
        return int(instance.view_count / instance.user_count)
    avg_count.short_description = "Avg Count"
    avg_count.allow_tags = True
    avg_count.is_column = True

    list_display = ('date', 'user_count', 'view_count', 'avg_count')
    list_display_links = ('date',)

    list_filter = ['date', 'user_count', 'view_count']
    actions = None
    aggregate_fields = {"user_count": "sum", 'view_count': "sum"}

    refresh_times = (3, 5, 10)
    data_charts = {
        "user_count": {'title': u"User Report", "x-field": "date", "y-field": ("user_count", "view_count"), "order": ('date',)},
        "avg_count": {'title': u"Avg Report", "x-field": "date", "y-field": ('avg_count',), "order": ('date',)},
        "per_month": {'title': u"Monthly Users", "x-field": "_chart_month", "y-field": ("user_count", ), 
                              "option": {
                                         "series": {"bars": {"align": "center", "barWidth": 0.8,'show':True}}, 
                                         "xaxis": {"aggregate": "sum", "mode": "categories"},
                                         },
                            },
    }
    
    def _chart_month(self,obj):
        return obj.date.strftime("%B")
        

xadmin.site.register(Host, HostAdmin)
xadmin.site.register(HostGroup, HostGroupAdmin)
xadmin.site.register(MaintainLog, MaintainLogAdmin)
xadmin.site.register(IDC, IDCAdmin)
xadmin.site.register(AccessRecord, AccessRecordAdmin)

# class MyModel2Admin(object):
#     pass
# #    relfield_style = 'fk-ajax'
# 
# xadmin.site.register(MyModel,MyModel2Admin)
# xadmin.site.register(MyModel2)

# import route
import pages
# import test_view
# import test_page

from xadmin.views.dashboard import AppDashboard

class DemoIndex(AppDashboard):
    app_label = 'app'
#     template = 'app_dashboard.html'
    
xadmin.site.register_appindex(DemoIndex)
# xadmin.site.register_view(r'^test_demo_index$', DemoIndex, name='DemoIndex')


class AuthIndex(AppDashboard):
    app_label = 'xadmin'
#     template = 'app_dashboard.html'
    
xadmin.site.register_appindex(AuthIndex)