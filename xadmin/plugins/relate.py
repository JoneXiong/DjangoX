# coding=utf-8
'''
模型关联相关
'''
from django.core.urlresolvers import reverse
from django.utils.encoding import force_unicode
from django.utils.encoding import smart_str
from django.utils.safestring import mark_safe
from django.db.models.sql.query import LOOKUP_SEP
from django.utils.translation import ugettext as _
from django.db import models

from xadmin.sites import site
from xadmin.views import BasePlugin, ListAdminView, CreateAdminView, UpdateAdminView, DeleteAdminView
from xadmin.dutils import RelatedObject

RELATE_PREFIX = '_rel_'


class RelateMenuPlugin(BasePlugin):
    '''
    外键相关菜单
    '''

    related_list = []
    use_related_menu = True
    use_op_menu = True

    @staticmethod
    def get_r_list(model):
        opts = model._meta
        return opts.get_all_related_objects() + opts.get_all_related_many_to_many_objects()

    def get_related_list(self):
        '''
        获取关联的对象
        '''
        if hasattr(self, '_related_acts'):
            return self._related_acts

        _related_acts = []

        _r_list = RelateMenuPlugin.get_r_list(self.model)
        for r in _r_list:
            if self.related_list and (r.get_accessor_name() not in self.related_list):
                continue

            if hasattr(r, 'opts'):
                _model = r.model
            else:
                _model = r.related_model
            if _model not in self.admin_site._registry.keys():
                continue

            has_view_perm = self.has_model_perm(_model, 'view')
            has_add_perm = self.has_model_perm(_model, 'add')
            if not (has_view_perm or has_add_perm):
                continue

            _related_acts.append((r, has_view_perm, has_add_perm))

        self._related_acts = _related_acts
        if len(_related_acts)>0:
            self.first_rel_url = self._list_url(_related_acts[0][0])
        return self._related_acts

    def _list_url(self,r):
        info = RelateMenuPlugin.get_r_model_info(r)
        list_url = reverse('%s:%s_%s_changelist' % (self.admin_site.app_name, info['label'], info['model_name']) )
        return "%s?%s="%( list_url, RELATE_PREFIX + info['lookup_name'] )

    @staticmethod
    def get_r_model_info(r):
        if hasattr(r, 'opts'):
            opts = r.opts
        else:
            opts = r.related_model._meta
        label = opts.app_label
        model_name = opts.module_name
        f = r.field
        rel_name = f.rel.get_related_field().name
        lookup_name = '%s__%s__exact' % (f.name, rel_name)
        verbose_name = force_unicode(opts.verbose_name)
        return {
            'label': label,
            'model_name': model_name,
            'lookup_name': lookup_name,
            'verbose_name': verbose_name
        }


    def related_link(self, instance):
        '''
        外键关联菜单列
        '''
        links = []
        for r, view_perm, add_perm in self.get_related_list():
            info = RelateMenuPlugin.get_r_model_info(r)
            label = info['label']
            model_name = info['model_name']
            lookup_name = info['lookup_name']
            verbose_name = info['verbose_name']

            _tojoin = [ '<li class="with_menu_btn">' ]

            if view_perm:
                list_url = reverse('%s:%s_%s_changelist' % (self.admin_site.app_name, label, model_name) )
                str1 = '<a href="%s?%s=%s" title="查看%s"><i class="icon fa fa-th-list"></i> %s</a>' %(
                                                                                                  list_url,
                                                                                                  RELATE_PREFIX + lookup_name, str(instance.pk),
                                                                                                  verbose_name,
                                                                                                  verbose_name
                                                                                                  )
            else:
                str1 = '<a><span class="text-muted"><i class="icon fa fa-blank"></i> %s</span></a>' % verbose_name
            _tojoin.append(str1)

            if add_perm:
                add_url = reverse('%s:%s_%s_add' % (self.admin_site.app_name, label, model_name) )
                str2 = '<a class="add_link dropdown-menu-btn" href="%s?%s=%s" title="添加%s"><i class="icon fa fa-plus pull-right"></i></a>' %(
                                                                                                  add_url,
                                                                                                  RELATE_PREFIX + lookup_name,
                                                                                                  str(instance.pk),
                                                                                                  verbose_name
                                                                                                  )
            else:
                str2 = ''
            _tojoin.append(str2)

            link = ''.join(_tojoin)
            links.append(link)
        ul_html = '<ul class="dropdown-menu" role="menu">%s</ul>' % ''.join(links)
        return '<div class="dropdown related_menu pull-right"><a title="%s" class="relate_menu dropdown-toggle" data-toggle="dropdown"><i class="icon fa fa-list"></i></a>%s</div>' % (_('Related Objects'), ul_html)
    related_link.short_description = '&nbsp;'
    related_link.allow_tags = True
    related_link.allow_export = False
    related_link.is_column = False

    def op_link(self, instance):
        _model = self.admin_view.model
        links = []
        if self.has_view_perm:
            links.append('''<a data-res-uri="%s" data-edit-uri="%s" rel="tooltip" title="%s" class="btn btn-info btn-xs details-handler" ><i class="fa fa-search-plus"></i> 查看</a>'''%(self.admin_view.get_url('detail',instance.pk),self.admin_view.get_url('change',instance.pk),instance))
        if self.has_change_perm:
            links.append('''<a href="%s" class="btn btn-success btn-xs" ><i class="fa fa-edit"></i> 修改</a>'''%self.admin_view.get_url('change',instance.pk))
        if self.has_delete_perm:
            links.append('''<a href="%s" class="btn btn-danger btn-xs" ><i class="fa fa-trash"></i> 删除</a>'''%self.admin_view.get_url('delete',instance.pk))
        return ' '.join(links)
    op_link.short_description = '&nbsp;'
    op_link.allow_tags = True
    op_link.allow_export = False
    op_link.is_column = False

    def get_list_display(self, list_display):
        self.has_view_perm = self.admin_view.has_permission('view')
        self.has_change_perm = self.admin_view.has_permission('change')
        self.has_delete_perm = self.admin_view.has_permission('delete')
        if self.use_op_menu:
            if self.has_view_perm or self.has_add_perm or self.has_change_perm:
                list_display.append('op_link')
                self.admin_view.op_link = self.op_link
        if self.use_related_menu and len(self.get_related_list()):
            list_display.append('related_link')
            self.admin_view.related_link = self.related_link
            self.admin_view.get_detail_url = self.get_first_rel_url

        return list_display

    def get_first_rel_url(self, obj):
        return self.first_rel_url + str(obj.pk)


class RelateObject(object):
    '''
    列表关联的外键对象信息封装
    '''

    def __init__(self, admin_view, lookup, value):
        self.admin_view = admin_view
        self.org_model = admin_view.model
        self.opts = admin_view.opts
        self.lookup = lookup
        self.value = value

        parts = lookup.split(LOOKUP_SEP)
        # 得到外键的字段
        field = self.opts.get_field_by_name(parts[0])[0]

        if not hasattr(field, 'rel') and not isinstance(field, RelatedObject):
            raise Exception(u'Relate Lookup field must a related field')
        # 得到外键到的模型 to_model
        if hasattr(field, 'rel'):
            self.to_model = field.rel.to
            self.rel_name = field.rel.get_related_field().name
            self.is_m2m = isinstance(field.rel, models.ManyToManyRel)
        else:
            self.to_model = field.model
            self.rel_name = self.to_model._meta.pk.name
            self.is_m2m = False
        # 得带当前外键关联的对象 to_objs
        _manager = self.to_model._default_manager
        if hasattr(_manager, 'get_query_set'):
            to_qs = _manager.get_query_set()
        else:
            to_qs = _manager.get_queryset()
        self.to_objs = to_qs.filter(**{self.rel_name: value}).all()

        self.field = field

    def filter(self, queryset):
        return queryset.filter(**{self.lookup: self.value})

    def get_brand_name(self):
        if len(self.to_objs) == 1:
            to_model_name = str(self.to_objs[0])
        else:
            to_model_name = force_unicode(self.to_model._meta.verbose_name)

        return mark_safe(u"<span class='rel-brand'>%s <i class='fa fa-caret-right'></i></span> %s" % (to_model_name, force_unicode(self.opts.verbose_name_plural)))

    def get_list_tabs(self):
        _r_list = RelateMenuPlugin.get_r_list(self.to_model)
        list_tabs = []
        for r in _r_list:
            _site = self.admin_view.admin_site
            if hasattr(r, 'opts'):
                _model = r.model
            else:
                _model = r.related_model
            if _model not in _site._registry.keys():
                continue
            info = RelateMenuPlugin.get_r_model_info(r)
            list_url = reverse('%s:%s_%s_changelist' % (_site.app_name, info['label'], info['model_name']) )
            r_list_url = "%s?%s=%s"%( list_url, RELATE_PREFIX + info['lookup_name'],self.to_objs[0].pk)
            list_tabs.append( (r_list_url, info['verbose_name']))
        return list_tabs


class BaseRelateDisplayPlugin(BasePlugin):

    def init_request(self, *args, **kwargs):
        self.relate_obj = None
        for k, v in self.request.GET.items():
            if smart_str(k).startswith(RELATE_PREFIX):
                self.relate_obj = RelateObject(
                    self.admin_view, smart_str(k)[len(RELATE_PREFIX):], v)
                break
        if self.relate_obj==None:
            for k, v in self.request.POST.items():
                if smart_str(k).startswith(RELATE_PREFIX):
                    self.relate_obj = RelateObject(
                        self.admin_view, smart_str(k)[len(RELATE_PREFIX):], v)
                    break
        return bool(self.relate_obj)

    def _get_relate_params(self):
        return RELATE_PREFIX + self.relate_obj.lookup, self.relate_obj.value

    def _get_input(self):
        return '<input type="hidden" name="%s" value="%s" />' % self._get_relate_params()

    def _get_url(self, url):
        return url + ('&' if url.find('?') > 0 else '?') + ('%s=%s' % self._get_relate_params())


class ListRelateDisplayPlugin(BaseRelateDisplayPlugin):
    '''
    列表视图增加外键信息显示
    '''

    def get_list_queryset(self, queryset):
        if self.relate_obj:
            queryset = self.relate_obj.filter(queryset)
        return queryset

    def get_object_url(self, url, result):
        return self._get_url(url)

    def get_context(self, context):
        self.admin_view.list_template = 'xadmin/views/model_list_rel.html'
        context['brand_name'] = self.relate_obj.get_brand_name()
        context['rel_objs'] = self.relate_obj.to_objs
        if 'add_url' in context:
            context['add_url'] = self._get_url(context['add_url'])
        context['rel_detail_url'] = self.admin_view.get_model_url(self.relate_obj.to_model,'detail',self.relate_obj.to_objs[0].id)
        self.admin_view.list_tabs = self.relate_obj.get_list_tabs()
        return context

    def get_list_display(self, list_display):
        if not self.relate_obj.is_m2m:
            try:
                list_display.remove(self.relate_obj.field.name)
            except Exception:
                pass
        return list_display


class EditRelateDisplayPlugin(BaseRelateDisplayPlugin):

    def get_form_datas(self, datas):
        if self.admin_view.org_obj is None and self.admin_view.request_method == 'get':
            datas['initial'][
                self.relate_obj.field.name] = self.relate_obj.value
        return datas

    def post_response(self, response):
        if isinstance(response, basestring) and response != self.get_admin_url('index'):
            return self._get_url(response)
        return response

    def get_context(self, context):
        if 'delete_url' in context:
            context['delete_url'] = self._get_url(context['delete_url'])
        return context

    def block_after_fieldsets(self, context, nodes):
        return self._get_input()


class DeleteRelateDisplayPlugin(BaseRelateDisplayPlugin):

    def post_response(self, response):
        if isinstance(response, basestring) and response != self.get_admin_url('index'):
            return self._get_url(response)
        return response

    def block_form_fields(self, context, nodes):
        return self._get_input()

site.register_plugin(RelateMenuPlugin, ListAdminView)
site.register_plugin(ListRelateDisplayPlugin, ListAdminView)
site.register_plugin(EditRelateDisplayPlugin, CreateAdminView)
site.register_plugin(EditRelateDisplayPlugin, UpdateAdminView)
site.register_plugin(DeleteRelateDisplayPlugin, DeleteAdminView)
