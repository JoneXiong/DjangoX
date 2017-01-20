# coding=utf-8

from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db import models
from django.utils.encoding import force_unicode, smart_unicode
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import ugettext as _
from django.utils.text import Truncator

from xadmin.util import lookup_field, display_for_field, label_for_field, boolean_icon
from xadmin.defs import TO_FIELD_VAR, ALL_VAR, ORDER_VAR, PAGE_VAR, COL_LIST_VAR, ERROR_FLAG, SEARCH_VAR, EMPTY_CHANGELIST_VALUE

from base import filter_hook, csrf_protect_m
from model_page import ModelPage
from common import FakeMethodField, ResultRow, ResultItem, ResultHeader
from grid import BaseGrid


class ListAdminView(BaseGrid,ModelPage):

    list_display = ('__str__',)    #: 列表字段
    list_exclude = ()              #: 排除显示的列, 在显示列的设置中不会出现这些被排除的列
    
    list_display_links = ()        #: 链接字段
    list_display_links_details = True  #: 链接到详情页面而非编辑页
    
    list_select_related = None     #: 是否提前加载关联数据, 使用 ``select_related``
    
    list_per_page = 50             #: 每页显示数据的条数
    list_max_show_all = 200        #: 每页最大显示数据的条数
    paginator_class = Paginator    #: 分页类

    search_fields = ()             #: 按照这些列搜索数据
    ordering = None                #: 默认的数据排序规则
    
    list_template = None    #: 显示数据的模板
    pop = False
    search_sphinx_ins = None 
    col_ctrl = True

    list_tabs = []

    def init_request(self, *args, **kwargs):
        """
        初始化请求, 首先判断当前用户有无 view 权限, 而后进行一些生成数据列表所需的变量的初始化操作.
        """
        if not self.has_view_permission():
            raise PermissionDenied

        request = self.request
        #request.session['LIST_QUERY'] = (self.model_info, self.request.META['QUERY_STRING'])

        self.list_display = self.get_list_display() #插件在其后起作用
        self.list_display_links = self.get_list_display_links()

        # 获取当前页码
        try:
            self.page_num = int(request.GET.get(PAGE_VAR, 0))
        except ValueError:
            self.page_num = 0

        # 获取各种参数
        self.show_all = ALL_VAR in request.GET
        self.to_field = request.GET.get(TO_FIELD_VAR)
        self.params = dict(request.GET.items())
        
        if 'pop' in self.request.GET:
            self.pop = True
            self.base_template = 'xadmin/base_pure.html'

        # 删除已经获取的参数, 因为后面可能要用 params 或过滤数据
        if PAGE_VAR in self.params:
            del self.params[PAGE_VAR]
        if ERROR_FLAG in self.params:
            del self.params[ERROR_FLAG]

    @filter_hook
    def get_list_display(self):
        u"""
        list_display 列表显示列
        base_list_display    原始的显示列 导出使用
        """
        self.base_list_display = ( COL_LIST_VAR in self.request.GET and self.request.GET[COL_LIST_VAR] != "" and \
            self.request.GET[COL_LIST_VAR].split('.') ) or self.list_display
        return list(self.base_list_display)

    @filter_hook
    def get_list_display_links(self):
        u"""
        用于显示链接的字段    修改链接/查看链接
        list_display_links
        """
        if self.list_display_links or not self.list_display:
            return self.list_display_links
        else:
            return list(self.list_display)[:1]

    @filter_hook
    def get_list_queryset(self):
        u"""
        取得模型查询结果集
        """
        # 首先取得基本的 queryset
        if self.search_sphinx_ins:
            query = self.request.GET.get(SEARCH_VAR, '')
            if query:
                query_set = self.search_sphinx_ins.query(query)
                query_set.set_options(mode='SPH_MATCH_EXTENDED2')
                query_set.set_options(rankmode='SPH_SORT_RELEVANCE')
                query_set.order_by('-@weight', '-@id')
                query_set._maxmatches = 500
                query_set._limit = 500
                
                sph_results = query_set._get_sphinx_results()
                result_ids = [r['id'] for r in sph_results['matches'][:500]]
                if query.isdigit():
                    result_ids.append(int(query))
                queryset = self.queryset().filter(id__in=result_ids)
            else:
                queryset = self.queryset()
        else:
            queryset = self.queryset()

        if not queryset.query.select_related:
            if self.list_select_related:
                queryset = queryset.select_related()
            elif self.list_select_related is None:
                related_fields = []
                for field_name in self.list_display:
                    try:
                        field = self.opts.get_field(field_name)
                    except models.FieldDoesNotExist:
                        pass
                    else:
                        if isinstance(field.rel, models.ManyToOneRel):
                            related_fields.append(field_name)
                if related_fields:
                    # 有关联字段显示, 则使用 ``select_related``
                    queryset = queryset.select_related(*related_fields)
            else:
                pass

        # 进行排序
        queryset = queryset.order_by(*self.get_ordering())
        
        return queryset



    @filter_hook
    def get_ordering_field(self, field_name):
        """
        验证排序字段 field_name 的有效性
        """
        try:
            field = self.opts.get_field(field_name)
            return field.name
        except models.FieldDoesNotExist:
            # 在非 db field 中获取
            if callable(field_name):
                attr = field_name
            elif hasattr(self, field_name):
                attr = getattr(self, field_name)
            else:
                attr = getattr(self.model, field_name)
            return getattr(attr, 'admin_order_field', None)

    @filter_hook
    def get_ordering(self):
        ordering = list(super(ListAdminView, self).get_ordering() or self._get_default_ordering())
        if ORDER_VAR in self.params and self.params[ORDER_VAR]:
            # Clear ordering and used params
            order_list = map( lambda p: p.rpartition('-'), self.params[ORDER_VAR].split('.') )
            ordering = []
            for __, pfx, field_name in order_list:
                check_name = self.get_ordering_field(field_name)
                if check_name:
                    ordering.append(pfx + check_name)

        pk_name = self.opts.pk.name
        if not (set(ordering) & set(['pk', '-pk', pk_name, '-' + pk_name])):
            ordering.append('-pk')
        return ordering


    def get_check_field_url(self, f):
        """
        返回 ``显示列`` 菜单项中每一项的 url. 
        """
        # 使用 :attr:`base_list_display` 作为基础列, 因为 :attr:`list_display` 可能已经被插件修改
        fields = [fd for fd in self.base_list_display if fd != f.name]
        if len(self.base_list_display) == len(fields):
            if f.primary_key:
                fields.insert(0, f.name)
            else:
                fields.append(f.name)
        return self.get_query_string({COL_LIST_VAR: '.'.join(fields)})

    def get_model_method_fields(self):
        u"""
        获得模型的方法型字段 （目前主要用在显示列的控制）
        is_column、short_description
        """
        methods = []
        for name in dir(self):
            try:
                if getattr(getattr(self, name), 'is_column', False):
                    methods.append((name, getattr(self, name)))
            except:
                pass
        return [FakeMethodField(name, getattr(method, 'short_description', capfirst(name.replace('_', ' '))))
                for name, method in methods]
        
    def get_model_fields(self):
        u'''
        获取所有可供显示的列的信息
        '''
        model_fields = [(f, f.name in self.list_display, self.get_check_field_url(f))
                        for f in (list(self.opts.fields) + self.get_model_method_fields()) if f.name not in self.list_exclude]
        return model_fields

    @filter_hook
    def get_context(self):
        """
        **Context Params** :

            ``model_fields`` : 用于 ``选择显示列`` 功能, 保存所有可显示的列信息

            ``result_headers`` : 显示列表的头部信息, 是 :class:`ResultHeader` 列表

            ``results`` : 显示列表的内容信息, 是 :class:`ResultItem` 列表
        """
        if hasattr(self, 'verbose_name'):
            self.opts.verbose_name = self.verbose_name
            self.opts.verbose_name_plural = self.verbose_name
        self.title = _('%s List') % force_unicode(self.opts.verbose_name)

        # 获取所有可供显示的列的信息
        model_fields = [(f, f.name in self.list_display, self.get_check_field_url(f))
                        for f in (list(self.opts.fields) + self.get_model_method_fields()) if f.name not in self.list_exclude]

        new_context = {
            'module_name': force_unicode(self.opts.verbose_name_plural),
            'title': self.title,
            'cl': self,
            'model_fields': self.get_model_fields(),
            'clean_select_field_url': self.get_query_string(remove=[COL_LIST_VAR]),
            'has_add_permission': self.has_add_permission(),
            'app_label': self.app_label,
            'brand_name': self.opts.verbose_name_plural,
            'brand_icon': self.get_model_icon(self.model),
            'add_url': self.model_admin_url('add'),
            'result_headers': self.result_headers(),
            'results': self.results(),
            'nav_buttons': mark_safe(' '.join(self.get_nav_btns()) ),
        }
        if self.list_tabs:
            cur_tab = self.request.GET.get('_tab','0')
            new_context['cur_tab'] = int(cur_tab)
        context = super(ListAdminView, self).get_context()
        context.update(new_context)
        return context

    @property
    def _tpl(self):
        return self.list_template or self.get_template_list('views/grid.html')

    @filter_hook
    def post_response(self, *args, **kwargs):
        """
        列表的 POST 请求, 该方法默认无返回内容, 插件可以复写该方法, 返回指定的 HttpResponse.
        """
        pass

    @csrf_protect_m
    @filter_hook
    def post(self, request, *args, **kwargs):
        """
        显示 Model 列表的 POST 请求, 默认跟 GET 请求返回同样的结果, 插件可以通过复写 :meth:`post_response` 方法改变 POST 请求的返回
        """
        return self.post_result_list() or self.post_response(*args, **kwargs) or self.get(request, *args, **kwargs)


    @filter_hook
    def result_header(self, field_name, row):
        """
        返回某一列的头信息, 一个 :class:`ResultHeader` 实例.

        :param field_name: 列的名字
        :param row: :class:`ResultHeader` 实例
        """
        ordering_field_columns = self.ordering_field_columns
        item = ResultHeader(field_name, row)
        text, attr = label_for_field(field_name, self.model,
                                     model_admin=self,
                                     return_attr=True
                                     )
        item.text = text
        item.attr = attr
        if attr and not getattr(attr, "admin_order_field", None):
            return item

        # 接下来就是处理列排序的问题了
        th_classes = ['sortable']
        order_type = ''
        new_order_type = 'desc'
        sort_priority = 0
        sorted = False
        # 判断当前列是否已经排序
        if field_name in ordering_field_columns:
            sorted = True
            order_type = ordering_field_columns.get(field_name).lower()
            sort_priority = ordering_field_columns.keys().index(field_name) + 1
            th_classes.append('sorted %sending' % order_type)
            new_order_type = {'asc': 'desc', 'desc': 'asc'}[order_type]

        # build new ordering param
        o_list_asc = []  # URL for making this field the primary sort
        o_list_desc = []  # URL for making this field the primary sort
        o_list_remove = []  # URL for removing this field from sort
        o_list_toggle = []  # URL for toggling order type for this field
        make_qs_param = lambda t, n: ('-' if t == 'desc' else '') + str(n)

        for j, ot in ordering_field_columns.items():
            if j == field_name:  # Same column
                param = make_qs_param(new_order_type, j)
                # We want clicking on this header to bring the ordering to the
                # front
                o_list_asc.insert(0, j)
                o_list_desc.insert(0, '-' + j)
                o_list_toggle.append(param)
                # o_list_remove - omit
            else:
                param = make_qs_param(ot, j)
                o_list_asc.append(param)
                o_list_desc.append(param)
                o_list_toggle.append(param)
                o_list_remove.append(param)

        if field_name not in ordering_field_columns:
            o_list_asc.insert(0, field_name)
            o_list_desc.insert(0, '-' + field_name)

        item.sorted = sorted
        item.sortable = True
        item.ascending = (order_type == "asc")
        item.sort_priority = sort_priority

        # 列排序菜单的内容
        menus = [
            ('asc', o_list_asc, 'caret-up', _(u'Sort ASC')),
            ('desc', o_list_desc, 'caret-down', _(u'Sort DESC')),
        ]
        if sorted:
            row['num_sorted_fields'] = row['num_sorted_fields'] + 1
            menus.append((None, o_list_remove, 'times', _(u'Cancel Sort')))
            item.btns.append('<a class="toggle" href="%s"><i class="fa fa-%s"></i></a>' % (
                self.get_query_string({ORDER_VAR: '.'.join(o_list_toggle)}), 'sort-up' if order_type == "asc" else 'sort-down'))

        item.menus.extend(['<li%s><a href="%s" class="active"><i class="fa fa-%s"></i> %s</a></li>' %
                         (
                             (' class="active"' if sorted and order_type == i[
                              0] else ''),
                           self.get_query_string({ORDER_VAR: '.'.join(i[1])}), i[2], i[3]) for i in menus])
        item.classes.extend(th_classes)

        return item

    @filter_hook
    def result_headers(self):
        """
        返回列表的列头信息. 返回一个 :class:`ResultRow` 实例, 其 ``cells`` 属性包含列信息
        """
        row = ResultRow()
        row['num_sorted_fields'] = 0
        row.cells = [self.result_header(
            field_name, row) for field_name in self.list_display]
        return row

    def get_detail_url(self,obj):
        return self.model_admin_url("detail", getattr(obj, self.pk_name))

    @filter_hook
    def result_item(self, obj, field_name, row):
        """
        返回某一对象某一列的数据, :class:`ResultItem` 实例.

        :param obj: Model 对象
        :param field_name: 列的名字
        :param row: :class:`ResultHeader` 实例
        """
        item = ResultItem(field_name, row) # 首先初始化
        field_name_split = field_name.split('.')
        field_name = field_name_split[0]
        try:
            f, attr, value = lookup_field(field_name, obj, self)
        except (AttributeError, ObjectDoesNotExist):
            item.text = mark_safe("<span class='text-muted'>%s</span>" % EMPTY_CHANGELIST_VALUE)
        else:
            if f is None:
                # Model 属性或是 OptionClass 属性列
                item.allow_tags = getattr(attr, 'allow_tags', False)
                boolean = getattr(attr, 'boolean', False)
                if boolean:
                    item.allow_tags = True
                    item.text = boolean_icon(value)
                else:
                    item.text = smart_unicode(value)
            else:
                # 处理关联咧
                if isinstance(f.rel, models.ManyToOneRel):
                    field_val = getattr(obj, f.name)
                    if field_val is None:
                        item.text = mark_safe("<span class='text-muted'>%s</span>" % EMPTY_CHANGELIST_VALUE)
                    else:
                        if len(field_name_split)>1:
                            item.text = getattr(field_val,field_name_split[1])
                        else:
                            item.text = field_val
                else:
                    item.text = display_for_field(value, f)
                if isinstance(f, models.DateField)\
                    or isinstance(f, models.TimeField)\
                        or isinstance(f, models.ForeignKey):
                    item.classes.append('nowrap')

            item.field = f
            item.attr = attr
            item.value = value

        # 如果没有指定 ``list_display_links`` , 使用第一列作为内容连接列.
        if (item.row['is_display_first'] and not self.list_display_links) \
                or field_name in self.list_display_links:
            item.row['is_display_first'] = False
            item.is_display_link = True
            if self.list_display_links_details:
                url = self.get_detail_url(obj)
                #item_res_uri = self.model_admin_url("detail", getattr(obj, self.pk_name))
                #if item_res_uri:
                #    edit_url = self.model_admin_url("change", getattr(obj, self.pk_name))
                #    item.wraps.append('<a data-res-uri="%s" data-edit-uri="%s" class="details-handler" rel="tooltip" title="%s">%%s</a>'
                #                     % (item_res_uri, edit_url, _(u'Details of %s') % str(obj)))
            else:
                url = self.get_object_url(obj)
            if self.pop:
                if 's' in self.request.GET:
                    show = getattr(obj, self.request.GET.get('s'))
                    if callable(show):show = show()
                else:
                    show = escape(Truncator(obj).words(14, truncate='...'))
                show = str(show).replace('%','%%').replace("\'","\\\'")
                pop = format_html(' class="for_multi_select" show="{0}" sid="{1}" ', show, getattr(obj, self.request.GET.get('t')) )
            else:
                pop = ''
            item.wraps.append(u'<a href="%s" %s>%%s</a>' % (url, pop))

        return item

    @filter_hook
    def result_row(self, obj):
        """
        返回列表某一行的内容信息. 返回一个 :class:`ResultRow` 实例, 其 ``cells`` 属性包含各列内容信息

        :param obj: Model 对象
        """
        row = ResultRow()
        row['is_display_first'] = True
        row['object'] = obj
        row.cells = [self.result_item(
            obj, field_name, row) for field_name in self.list_display]
        return row

    @filter_hook
    def results(self):
        """
        返回整个列表内容信息. 返回一个 :class:`ResultRow` 的数据, 包含各行信息
        """
        results = []
        for obj in self.result_list:
            results.append(self.result_row(obj))
        return results


