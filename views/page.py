# coding=utf-8

from django.template.response import SimpleTemplateResponse
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from django.core.paginator import InvalidPage, Paginator
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.utils.html import escape, conditional_escape

import xadmin
from base import BaseAdminView, CommAdminView, filter_hook, inclusion_tag, csrf_protect_m
from form import FormAdminView
from list import ResultRow, ResultItem, ResultHeader, COL_LIST_VAR

DOT = '.'
PAGE_VAR = 'p'

class PageView(CommAdminView):
    verbose_name = None
    template = 'xadmin/views/page.html'
    
    app_label = 'xadmin'
    menu_group = '_default_group'
    icon_class = 'fa fa-plus'
    #menu_index = 0
    order = 0
    
    hidden_menu = False
    perm = None#'comm_page_code'
    
    def init_request(self, *args, **kwargs):
        #if not self.perm:
        #   self.perm = self.__class__.__name__
        if self.perm:
            if not self.user.has_perm('auth.'+self.perm):
                raise PermissionDenied
    
    def get(self, request, *args, **kwargs):
        return TemplateResponse(self.request,self.template, self.get_context())
    
    def get_content(self):
        pass
    
    def get_context(self):
        context = super(PageView, self).get_context()
        context.update({
                        'content': self.get_content() or '',
                        'title': self.verbose_name or self.__class__.__bases__ [0].__name__,
                        })
        return context
    
    @classmethod 
    def get_page_url(cls):
        m_root = xadmin.ROOT_PATH_NAME and '/'+xadmin.ROOT_PATH_NAME or ''
        return '%s/page/%s/'%(m_root, cls.__name__.lower())
    
class FormPage(FormAdminView,PageView):
    pass

    @classmethod  
    def render_btn(cls, _redirect=None):
        m_root = xadmin.ROOT_PATH_NAME and '/'+xadmin.ROOT_PATH_NAME or ''
        if _redirect:
            return '<a href="%s/page/%s/?_redirect=%s" class="btn btn-primary"><i class="%s"></i> %s</a>'%( m_root, cls.__name__.lower(), _redirect, cls.icon_class, cls.verbose_name )
        else:
            return '<a href="%s/page/%s/" class="btn btn-primary"><i class="%s"></i> %s</a>'%( m_root, cls.__name__.lower(), cls.icon_class, cls.verbose_name )

class GridPage(PageView):
    template = 'xadmin/views/grid.html'
    icon_class = 'fa fa-circle-o'
    
    list_filter = ()
    
    list_display_links_details = False
    
    list_per_page = 30             #: 每页显示数据的条数
    list_max_show_all = 200        #: 每页最大显示数据的条数
    paginator_class = Paginator    #: 分页类
    
    result_count = 3
    result_list = [1,2,3,4,5]
    
    actions = []
    opts = 'sdfas'
    list_display = ('__str__',)    #: 默认显示列
    
    head = []
    col_ctrl = True
    
#    brand_icon
#    brand_name
#    
#    model_fields
#    
#    results
#    result_headers

    @filter_hook
    def get_list_display(self):
        self.base_list_display = (COL_LIST_VAR in self.request.GET and self.request.GET[COL_LIST_VAR] != "" and \
            self.request.GET[COL_LIST_VAR].split('.')) or [e[0] for e in self.head]
        return list(self.base_list_display)

    def init_request(self, *args, **kwargs):
#        if not self.has_view_permission():
#            raise PermissionDenied
        
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
                        'brand_icon': self.icon_class,
                        'model_fields': self.model_fields(),
                        'result_headers': self.result_headers(),
                        'results': self.results() or [],
                        'nav_buttons': mark_safe(''.join(self.get_nav_btns()) ),
                        'col_ctrl': self.col_ctrl
                        })
        return context
    
    @filter_hook
    def get_response(self, context, *args, **kwargs):
        """
        在 :meth:`get_context` 之后执行. 该方法默认无返回内容, 插件可以复写该方法, 返回指定的 HttpResponse.
        """
        pass
    
    @csrf_protect_m
    @filter_hook
    def get(self, request, *args, **kwargs):
        """
        显示 Model 列表. 
        """
        # 首选获取列表 result_list
        response = self.get_result_list()
        if response:
            return response

        context = self.get_context()
        context.update(kwargs or {})

        response = self.get_response(context, *args, **kwargs)

        return response or TemplateResponse(request, self.template, context, current_app=self.admin_site.name)

    @filter_hook
    def get_media(self):
        """
        返回列表页面的 Media, 该页面添加了 ``xadmin.page.list.js`` 文件
        """
        media = super(GridPage, self).get_media() + self.vendor('xadmin.page.list.js', 'xadmin.page.form.js')
        if self.list_display_links_details:
            media += self.vendor('xadmin.plugin.details.js', 'xadmin.form.css')
        return media
    
    @filter_hook
    def get_result_list(self):
        '''
        GET 请求时返回的列表数据
        '''
        return self.make_result_list()

    @filter_hook
    def post_result_list(self):
        '''
        POST 请求时返回的列表数据
        '''
        return self.make_result_list()
    
    @filter_hook
    def result_headers(self):
        """
        返回列表的列头信息. 返回一个 :class:`ResultRow` 实例, 其 ``cells`` 属性包含列信息
        """
        row = ResultRow()
        row['num_sorted_fields'] = 0
        for field_name, text in self.head:
            m_rh = ResultHeader(field_name, row)
            m_rh.text = text
            row.cells.append(m_rh)
        check_box_rh = ResultHeader('action_checkbox', row)
        check_box_rh.text = '<input type="checkbox" id="action-toggle">'
        check_box_rh.classes.append("action-checkbox-column")
        row.cells.insert(0,check_box_rh)
        return row
    
    @filter_hook
    def get_paginator(self):
        """
        返回 paginator 实例, 使用 :attr:`paginator_class` 类实例化
        """
        return self.paginator_class(self.list_queryset, self.list_per_page, 0, True)

    def model_fields(self):
        return [ ({"verbose_name": text}, True, '?_cols='+field_name) for field_name, text in self.head  ]
    
    @filter_hook
    def get_list_queryset(self):
#        row = ResultRow()
#        row.add_cell('id', 1)
#        row.add_cell('tag', 2)
#        row.add_cell('alias', 3)
#        row.add_cell('vtalk_c', 4)
#        rows = [row,row,row,row,row]
        
        data = [
                {'id':1, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':2, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':3, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':4, 'tag':2, 'alias':3, 'vtalk_c':4},
                {'id':5, 'tag':2, 'alias':3, 'vtalk_c':4},
                ]
        from xadmin.db.query import Collection
        return Collection(data)
        #return rows
    
    @filter_hook
    def results(self):
        """
        返回整个列表内容信息. 返回一个 :class:`ResultRow` 的数据, 包含各行信息
        """
        results = []
        for data in self.result_list:
            row = ResultRow()
            for key in self.list_display:
                if key!='action_checkbox':
                    row.add_cell(key, data[key])
            results.append(row)
        return results
        #return self.result_list
    
    def make_result_list(self):
#        row = ResultRow()
#        row.add_cell('id', 1)
#        row.add_cell('tag', 2)
#        row.add_cell('alias', 3)
#        row.add_cell('vtalk_c', 4)
#        
#        rows = [row,row,row,row,row]
        self.list_queryset = self.get_list_queryset()
        self.paginator = self.get_paginator()
        
        # 获取当前据数目
        self.result_count = self.paginator.count
        self.full_result_count = self.result_count
        
        self.can_show_all = self.result_count <= self.list_max_show_all
        self.multi_page = self.result_count > self.list_per_page
        
        if (self.show_all and self.can_show_all) or not self.multi_page:
            self.result_list = self.list_queryset
        else:
            try:
                self.result_list = self.paginator.page(
                    self.page_num + 1).object_list
            except InvalidPage:
                # 分页错误, 这里的错误页面需要调整一下
                if 'e' in self.request.GET.keys():
                    return SimpleTemplateResponse('xadmin/views/invalid_setup.html', {
                        'title': _('Database error'),
                    })
                return HttpResponseRedirect(self.request.path + '?' + ERROR_FLAG + '=1')
        self.has_more = self.result_count > (  self.list_per_page * self.page_num + len(self.result_list) )

    
    def get_nav_btns(self):
        return []
    
    def get_url(self):
        m_root = xadmin.ROOT_PATH_NAME and '/'+xadmin.ROOT_PATH_NAME or ''
        return '%s/page/%s/'%(m_root, self.__class__.__bases__ [0].__name__.lower())

    def get_page_number(self, i):
        """
        返回翻页组件各页码显示的 HTML 内容. 默认使用 bootstrap 样式

        :param i: 页码, 可能是 ``DOT``
        """
        if i == DOT:
            return mark_safe(u'<span class="dot-page">...</span> ')
        elif i == self.page_num:
            return mark_safe(u'<span class="this-page">%d</span> ' % (i + 1))
        else:
            return mark_safe(u'<a href="%s"%s>%d</a> ' % (escape(self.get_query_string({PAGE_VAR: i})), (i == self.paginator.num_pages - 1 and ' class="end"' or ''), i + 1))


    @inclusion_tag('xadmin/includes/pagination.html')
    def block_pagination(self, context, nodes, page_type='normal'):
        paginator, page_num = self.paginator, self.page_num

        pagination_required = (
            not self.show_all or not self.can_show_all) and self.multi_page
        if not pagination_required:
            page_range = []
        else:
            ON_EACH_SIDE = {'normal': 5, 'small': 3}.get(page_type, 3)
            ON_ENDS = 2

            # If there are 10 or fewer pages, display links to every page.
            # Otherwise, do some fancy
            if paginator.num_pages <= 10:
                page_range = range(paginator.num_pages)
            else:
                # Insert "smart" pagination links, so that there are always ON_ENDS
                # links at either end of the list of pages, and there are always
                # ON_EACH_SIDE links at either end of the "current page" link.
                page_range = []
                if page_num > (ON_EACH_SIDE + ON_ENDS):
                    page_range.extend(range(0, ON_EACH_SIDE - 1))
                    page_range.append(DOT)
                    page_range.extend(
                        range(page_num - ON_EACH_SIDE, page_num + 1))
                else:
                    page_range.extend(range(0, page_num + 1))
                if page_num < (paginator.num_pages - ON_EACH_SIDE - ON_ENDS - 1):
                    page_range.extend(
                        range(page_num + 1, page_num + ON_EACH_SIDE + 1))
                    page_range.append(DOT)
                    page_range.extend(range(
                        paginator.num_pages - ON_ENDS, paginator.num_pages))
                else:
                    page_range.extend(range(page_num + 1, paginator.num_pages))

        need_show_all_link = self.can_show_all and not self.show_all and self.multi_page
        return {
            'cl': self,
            'pagination_required': pagination_required,
            'show_all_url': need_show_all_link and self.get_query_string({'all': ''}),
            'page_range': map(self.get_page_number, page_range),
            'ALL_VAR': 'all',
            '1': 1,
        }
    
class FormAction(FormPage):
    pass