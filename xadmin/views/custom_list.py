# coding=utf-8

import json
import urllib

from django.core.paginator import Paginator, Page
from django.utils.safestring import mark_safe
from django.template import loader

import xadmin
from base import filter_hook
from list import ResultRow, ResultHeader, COL_LIST_VAR, ResultItem
from xadmin.db.query import Collection
from grid import BaseGrid

from custom_page import PageView

class RpcPaginator(Paginator):

    def page(self, number):
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        return Page(self.object_list.get_slice(bottom,self.per_page), number, self)

class GridPage(BaseGrid,PageView):
    template = 'xadmin/views/grid.html'
    icon = 'fa fa-circle-o'
    
    list_filter = ()
    search_fields = ()
    
    list_display_links_details = False
    form_actions = ()
    val_list = ()
    
    list_per_page = 30             #: 每页显示数据的条数
    list_max_show_all = 200        #: 每页最大显示数据的条数
    paginator_class = RpcPaginator    #: 分页类
    queryset_class = Collection
    
    actions = []

    list_display = ('__str__',)    #: 默认显示列
    
    head = []
    col_ctrl = True
    
    pop = False
    search_sphinx_ins = True
    
    _meta = None

    opts = None
    ordering = None

    @filter_hook
    def get_list_display(self):
        self.base_list_display = (COL_LIST_VAR in self.request.GET and self.request.GET[COL_LIST_VAR] != "" and \
            self.request.GET[COL_LIST_VAR].split('.')) or [e[0] for e in self.head]
        return list(self.base_list_display)

    def init_request(self, *args, **kwargs):
        super(GridPage, self).init_request(*args, **kwargs)
        
        request = self.request
        
        self.list_display = self.get_list_display()
        
        # 获取当前页码
        try:
            self.page_num = int(request.GET.get('p', 0))
        except ValueError:
            self.page_num = 0
            
        # 获取各种参数
        self.show_all = 'all' in request.GET
        #self.to_field = request.GET.get(TO_FIELD_VAR)
        self.params = dict(request.GET.items())
        
        # 删除已经获取的参数, 因为后面可能要用 params 或过滤数据
        if 'p' in self.params:
            del self.params['p']
        if 'e' in self.params:
            del self.params['e']
        
    def has_permission(self, perm_code):
        return True
    
    def get_context(self):
        context = super(GridPage, self).get_context()
        context.update({
                        'cl': self,
                        'brand_icon': self.icon,
                        'brand_name': context.get('title',''),
                        'model_fields': self.get_model_fields(),
                        'result_headers': self.result_headers(),
                        'results': self.results() or [],
                        'nav_buttons': mark_safe(' '.join(self.get_nav_btns()) ),
                        })
        return context
    
#     @filter_hook
#     def get_media(self):
#         media = super(GridPage, self).get_media() 
#         if self.check_box:
#             media += self.vendor('xadmin.plugin.actions.js', 'xadmin.plugins.css', 'xadmin.form.css')
#         return media

    @filter_hook
    def result_header(self, field_name, row):
        item = ResultHeader(field_name, row)
        return item
    
    @filter_hook
    def result_headers(self):
        """
        返回列表的列头信息. 返回一个 :class:`ResultRow` 实例, 其 ``cells`` 属性包含列信息
        """
        row = ResultRow()
        row['num_sorted_fields'] = 0
        _dict = dict(self.head)
        for field_name in self.list_display:
            if field_name!='action_checkbox':
                text = _dict[field_name]
            else:
                text = self.action_checkbox.short_description
            m_rh = self.result_header(field_name, row)
            m_rh.text = text
            row.cells.append(m_rh)
#         if self.check_box:
#             check_box_rh = ResultHeader('action_checkbox', row)
#             check_box_rh.text = '<input type="checkbox" id="action-toggle">'
#             check_box_rh.classes.append("action-checkbox-column")
#             row.cells.insert(0,check_box_rh)
        return row

    def get_model_fields(self):
        return [ ({"verbose_name": text}, True, '?_cols='+field_name) for field_name, text in self.head  ]
    
    @filter_hook
    def get_list_queryset(self):
        return self.queryset_class([])
    
    @filter_hook
    def get_ordering(self):
        return []
    
    def pk(self, data):
        m_data = {}
        for e in self.val_list:
            m_data[e] = data[e]
        return urllib.quote( json.dumps(m_data) )
    
    @filter_hook
    def result_item(self, obj, field_name, row):
        data = obj
        key = field_name
        
        item = ResultItem(field_name, row)
        if data.has_key(key):
            text = data[key]
        else:
            text = getattr(self, key)(data)
        item.text = text
        return item
    
    @filter_hook
    def result_row(self, obj):
        data = obj
        row = ResultRow()
        data['_pk'] = self.pk(data)
#             row.add_cell('_data', data['_pk'])
        for key in self.list_display:
#                 if key!='action_checkbox':
            row.cells.append(self.result_item(obj, key, row))
        return row
    
    @filter_hook
    def results(self):
        """
        返回整个列表内容信息. 返回一个 :class:`ResultRow` 的数据, 包含各行信息
        """
        results = []
        for data in self.result_list:
            results.append(self.result_row(data))
        return results
        #return self.result_list
        
    def select_addition(self, id, show):
        from django.utils.html import format_html
        return format_html(' class="for_multi_select" show="{0}" sid="{1}" ', show, id)

        
    # Block Views
#     def block_results_bottom(self, context, nodes):
#         if self.check_box and self.result_count:
#             nodes.append(loader.render_to_string('xadmin/blocks/grid.results_bottom.actions.html', context_instance=context))
    