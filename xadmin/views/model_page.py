# coding=utf-8

from django.core.paginator import Paginator
from django.utils.encoding import force_unicode
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

from base import SiteView, filter_hook

class ModelPage(SiteView):
    """
    基于 Model 的 页面
    注册后，用户可以通过访问 ``/%(app_label)s/%(module_name)s/123/test`` 访问到该view
    """

    opts = None
    model = None     #: 绑定的 Model 类，在注册 Model 时，该项会自动附在 OptionClass 中，见方法 :meth:`AdminSite.register`
    app_label = None
    module_name = None
    model_info = None
    
    remove_permissions = []
    exclude = None #用在编辑页或详情页
    fields = None #用在编辑页或详情页

    def __init__(self, request, *args, **kwargs):
        self.opts = self.model._meta
        self.app_label = self.app_label or self.model._meta.app_label
        self.module_name = self.model._meta.module_name
        self.model_info = (self.model._meta.app_label, self.module_name)

        super(ModelAdminView, self).__init__(request, *args, **kwargs)

    @filter_hook
    def get_context(self):
        new_context = {
            "opts": self.opts,
            "app_label": self.app_label,
            "module_name": self.module_name,
            "verbose_name": force_unicode(self.opts.verbose_name),
            'model_icon': self.get_model_icon(self.model),
        }
        context = super(ModelAdminView, self).get_context()
        context.update(new_context)
        return context

    @filter_hook
    def get_breadcrumb(self): 
        u'''
        导航链接基础部分
        '''
        bcs = super(ModelAdminView, self).get_breadcrumb()
        item = {'title': self.opts.verbose_name_plural}
        if self.has_view_permission():
            item['url'] = self.model_admin_url('changelist')
        bcs.append(item)
        return bcs

    @filter_hook
    def get_object(self, object_id):
        u"""
        根据 object_id 获得唯一的 Model 实例
        """
        queryset = self.queryset()
        model = queryset.model
        try:
            object_id = model._meta.pk.to_python(object_id)
            return queryset.get(pk=object_id)
        except (model.DoesNotExist, ValidationError):
            return None

    @filter_hook
    def get_object_url(self, obj):
        u'''
        对象链接
        '''
        if self.has_change_permission(obj):
            return self.model_admin_url("change", getattr(obj, self.opts.pk.attname))
        elif self.has_view_permission(obj):
            return self.model_admin_url("detail", getattr(obj, self.opts.pk.attname))
        else:
            return None
        
    def get_url(self, name, *args, **kwargs):
        u'''
        模型相关url
        eg  get_url( 'change', id )    get_url( 'detail', id )    get_url( 'chart', id )    get_url( 'patch', id )    get_url( 'revision', id,  vid)
              get_url( 'changelist' )    get_url( 'add' )    get_url( 'delete', id )
        '''
        return reverse(
            "%s:%s_%s_%s" % (self.admin_site.app_name, self.opts.app_label,
            self.module_name, name), args=args, kwargs=kwargs)

    def model_admin_url(self, name, *args, **kwargs):
        return self.get_url(name, *args, **kwargs)

    def get_template_list(self, template_name):
        opts = self.opts
        return (
            "xadmin/%s/%s/%s" % (opts.app_label, opts.object_name.lower(), template_name),
            "xadmin/%s/%s" % (opts.app_label, template_name),
            "xadmin/%s" % template_name,
        )

    def get_ordering(self):
        u"""
        模型的默认数据集排序规则
        """
        return self.ordering or ()
        
    def queryset(self):
        u"""
        模型的默认数据集
        """
        _manager = self.model._default_manager
        if hasattr(_manager, 'get_query_set'):
            return _manager.get_query_set()
        else:
            return _manager.get_queryset()

    def has_view_permission(self, obj=None):
        return ('view' not in self.remove_permissions) and (self.user.has_perm('%s.view_%s' % self.model_info) or self.user.has_perm('%s.change_%s' % self.model_info))

    def has_add_permission(self):
        return ('add' not in self.remove_permissions) and self.user.has_perm('%s.add_%s' % self.model_info)

    def has_change_permission(self, obj=None):
        return ('change' not in self.remove_permissions) and self.user.has_perm('%s.change_%s' % self.model_info)

    def has_delete_permission(self, obj=None):
        return ('delete' not in self.remove_permissions) and self.user.has_perm('%s.delete_%s' % self.model_info)

    def has_permission(self, perm_code):
        raw_code = perm_code[:]
        if perm_code in ('view', 'add', 'change', 'delete'):
            perm_code = '%s.%s_%s' %(self.model._meta.app_label, perm_code ,self.module_name)
        return (raw_code not in self.remove_permissions) and self.user.has_perm(perm_code)
    
    def get_model_perms(self):
        return {
            'view': self.has_view_permission(),
            'add': self.has_add_permission(),
            'change': self.has_change_permission(),
            'delete': self.has_delete_permission(),
        }
        
    @property
    def pk_name(self):
        return self.opts.pk.attname
        
ModelAdminView = ModelPage
ModelView = ModelAdminView

class ModelAdmin(object):
    
    # 【列表页】相关配置项
    
    list_display = ('__str__',)    #: 列表字段
    list_exclude = ()              #: 排除显示的列
    
    list_display_links = ()        #: 链接字段
    list_display_links_details = False  #: 链接到详情页面而非编辑页
    
    list_select_related = None     #: 是否提前加载关联数据, 使用 ``select_related``
    
    list_per_page = 50             #: 每页数
    list_max_show_all = 200        #: 当点“显示全部”每页显示的最大条数
    paginator_class = Paginator    #: 默认的分页类

    search_fields = ()             #: 按照这些列搜索数据
    ordering = None                #: 默认的数据排序

    list_template = None    #: 显示数据的模板 默认为 views/grid.html
    pop = False # 是否为弹窗页
    search_sphinx_ins = None # 使用的搜索引擎
    
    
    relfield_style = 'fk-ajax'
    
    # 【列表页】相关可获取项
    page_num = 0    # 当前第几页
    paginator = None    #分页类实例
    result_count = None #总记录数

    list_tabs = [] #列表页tab配置
