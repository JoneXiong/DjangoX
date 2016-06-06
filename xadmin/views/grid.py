# coding=utf-8

from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.template.response import SimpleTemplateResponse, TemplateResponse
from django.core.paginator import InvalidPage
from django.http import HttpResponseRedirect

from base import inclusion_tag, filter_hook, csrf_protect_m
from xadmin.defs import ALL_VAR, DOT
from xadmin import defs
from xadmin.core.structs import SortedDict

class BaseGrid(object):
    
    can_show_all = False # 默认隐藏"显示所有"链接
    select_close = True
    
    grid = True
    
    # 内部成员，不用于配置
    result_count = None # grid总条数
    result_list = None # 当前页记录集
    
    @property
    def _tpl(self):
        return self.template
    
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

        return response or TemplateResponse(request, self._tpl, context, current_app=self.admin_site.name)
    
    def _get_default_ordering(self):
        ordering = []
        if self.ordering:
            ordering = self.ordering
        elif self.opts:
            if self.opts.ordering:
                ordering = self.opts.ordering
        return ordering
    
    @filter_hook
    def get_ordering_field_columns(self):
        """
        从请求参数中得到排序信息 eg o=-create_time.status.-intro.title
        """
        ordering = self._get_default_ordering()
        ordering_fields = SortedDict()
        if defs.ORDER_VAR not in self.params or not self.params[defs.ORDER_VAR]:
            for field in ordering:
                if field.startswith('-'):
                    field = field[1:]
                    order_type = 'desc'
                else:
                    order_type = 'asc'
                for attr in self.list_display:
                    if self.get_ordering_field(attr) == field:
                        ordering_fields[field] = order_type
                        break
        else:
            for p in self.params[defs.ORDER_VAR].split('.'):
                __, pfx, field_name = p.rpartition('-')
                ordering_fields[field_name] = 'desc' if pfx == '-' else 'asc'
        return ordering_fields
    
    @filter_hook
    def get_paginator(self):
        """
        返回 paginator 实例
        """
        return self.paginator_class(self.list_queryset, self.list_per_page, 0, True)
    
    @filter_hook
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
            return mark_safe(u'<a href="%s"%s>%d</a> ' % (escape(self.get_query_string({defs.PAGE_VAR: i})), (i == self.paginator.num_pages - 1 and ' class="end"' or ''), i + 1))
    
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

            # 10页以内显示每页的链接
            if paginator.num_pages <= 10:
                page_range = range(paginator.num_pages)
            else:
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
            'show_all_url': need_show_all_link and self.get_query_string({ALL_VAR: ''}),
            'page_range': map(self.get_page_number, page_range),
            'ALL_VAR': ALL_VAR,
            '1': 1,
        }
        
    def make_result_list(self):
        u"""
        生成列表页结果数据
        result_list
        """
        # 排序及过滤等处理后的 queryset
        self.list_queryset = self.get_list_queryset()
        self.ordering_field_columns = self.get_ordering_field_columns()
        self.paginator = self.get_paginator()

        # 获取当前据数目
        self.result_count = self.paginator.count
        if self.can_show_all:
            self.can_show_all = self.result_count <= self.list_max_show_all
        self.multi_page = self.result_count > self.list_per_page

        if (self.show_all and self.can_show_all) or not self.multi_page:
            self.result_list = self.list_queryset._clone(count=self.result_count)
        else:
            try:
                self.result_list = self.paginator.page(
                    self.page_num + 1).object_list
            except InvalidPage:
                # 分页错误, 这里的错误页面需要调整一下
                if defs.ERROR_FLAG in self.request.GET.keys():
                    return SimpleTemplateResponse('xadmin/views/invalid_setup.html', {
                        'title': _('Database error'),
                    })
                return HttpResponseRedirect(self.request.path + '?' + defs.ERROR_FLAG + '=1')
        self.has_more = self.result_count > (
            self.list_per_page * self.page_num + len(self.result_list))
        
    @filter_hook
    def get_media(self):
        """
        返回列表页面的 Media, 该页面添加了 ``xadmin.page.list.js`` 文件
        """
        media = super(BaseGrid, self).get_media() + self.vendor('xadmin.page.list.js', 'xadmin.page.form.js', 'xadmin.form.css')
        if self.list_display_links_details:
            media += self.vendor('xadmin.plugin.details.js')
        return media
    
    def get_model_fields(self):
        return []
    
    
    def get_nav_btns(self):
        return []