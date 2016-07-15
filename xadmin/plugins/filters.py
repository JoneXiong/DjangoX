# coding=utf-8
"""
数据过滤器
list_filter
search_fields
free_query_filter
"""
import copy

import operator
from xadmin import widgets

from xadmin.util import get_fields_from_path, lookup_needs_distinct
from django.core.exceptions import SuspiciousOperation, ImproperlyConfigured, ValidationError
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.models.sql.query import LOOKUP_SEP, QUERY_TERMS
from django.template import loader
from django.utils.encoding import smart_str
from django.utils.translation import ugettext as _

from xadmin.filters import manager as filter_manager, DateFieldListFilter, RelatedFieldSearchFilter, MultiSelectFieldListFilter
from xadmin.sites import site
from xadmin.views import BasePlugin, ListAdminView
from xadmin.views.page import GridPage
from xadmin.defs import FILTER_PREFIX, SEARCH_VAR
from xadmin.dutils import RelatedObject

class IncorrectLookupParameters(Exception):
    pass


class FilterPlugin(BasePlugin):
    list_filter = ()
    search_fields = ()
    free_query_filter = True

    def lookup_allowed(self, lookup, value):
        model = self.model
        # Check FKey lookups that are allowed, so that popups produced by
        # ForeignKeyRawIdWidget, on the basis of ForeignKey.limit_choices_to,
        # are allowed to work.
        for l in model._meta.related_fkey_lookups:
            for k, v in widgets.url_params_from_lookup_dict(l).items():
                if k == lookup and v == value:
                    return True

        parts = lookup.split(LOOKUP_SEP)

        # Last term in lookup is a query term (__exact, __startswith etc)
        # This term can be ignored.
        if len(parts) > 1 and parts[-1] in QUERY_TERMS:
            parts.pop()

        # Special case -- foo__id__exact and foo__id queries are implied
        # if foo has been specificially included in the lookup list; so
        # drop __id if it is the last part. However, first we need to find
        # the pk attribute name.
        rel_name = None
        for part in parts[:-1]:
            try:
                field, _, _, _ = model._meta.get_field_by_name(part)
            except FieldDoesNotExist:
                # Lookups on non-existants fields are ok, since they're ignored
                # later.
                return True
            if hasattr(field, 'rel'):
                model = field.rel.to
                rel_name = field.rel.get_related_field().name
            elif isinstance(field, RelatedObject):
                model = field.model
                rel_name = model._meta.pk.name
            else:
                rel_name = None
        if rel_name and len(parts) > 1 and parts[-1] == rel_name:
            parts.pop()

        if len(parts) == 1:
            return True
        clean_lookup = LOOKUP_SEP.join(parts)
        return clean_lookup in self.list_filter

    def get_list_queryset(self, queryset):
        # 获得查询参数数据
        lookup_params = dict([(smart_str(k)[len(FILTER_PREFIX):], v) for k, v in self.admin_view.params.items()
                              if smart_str(k).startswith(FILTER_PREFIX) and v != ''])
        for p_key, p_val in lookup_params.iteritems():
            if p_val == "False":
                lookup_params[p_key] = False
        #
        use_distinct = False

        # for clean filters
        self.admin_view.has_query_param = bool(lookup_params)
        self.admin_view.clean_query_url = self.admin_view.get_query_string(remove=
                                                                           [k for k in self.request.GET.keys() if k.startswith(FILTER_PREFIX)])

        # Normalize the types of keys
        if not self.free_query_filter:
            for key, value in lookup_params.items():
                if not self.lookup_allowed(key, value):
                    raise SuspiciousOperation(
                        "Filtering by %s not allowed" % key)

        self.filter_specs = []
        if self.list_filter:
            for list_filter in self.list_filter:
                if callable(list_filter):
                    # 自定义过滤器
                    spec = list_filter(self.request, lookup_params,
                                       self.model, self)
                else:
                    field_path = None
                    field_parts = []
                    if isinstance(list_filter, (tuple, list)):
                        # This is a custom FieldListFilter class for a given field.
                        field, field_list_filter_class = list_filter
                    else:
                        # This is simply a field name, so use the default
                        # FieldListFilter class that has been registered for
                        # the type of the given field.
                        field, field_list_filter_class = list_filter, filter_manager.create
                    if not isinstance(field, models.Field):
                        field_path = field
                        field_parts = get_fields_from_path(
                            self.model, field_path)
                        field = field_parts[-1]
                    spec = field_list_filter_class(
                        field, self.request, lookup_params,
                        self.model, self.admin_view, field_path=field_path)

                    if len(field_parts)>1:
                        # Add related model name to title
                        spec.title = "%s %s"%(field_parts[-2].name,spec.title)

                    # Check if we need to use distinct()
                    use_distinct = (use_distinct or
                                    lookup_needs_distinct(self.opts, field_path))
                if spec and spec.has_output():
                    try:
                        new_qs = spec.do_filte(queryset)
                    except ValidationError, e:
                        new_qs = None
                        self.admin_view.message_user(_("<b>Filtering error:</b> %s") % e.messages[0], 'error')
                    if new_qs is not None:
                        queryset = new_qs

                    self.filter_specs.append(spec)

        self.has_filters = bool(self.filter_specs)
        self.admin_view.filter_specs = self.filter_specs
        self.admin_view.used_filter_num = len(
            filter(lambda f: f.is_used, self.filter_specs))

        try:
            for key, value in lookup_params.items():
                use_distinct = (
                    use_distinct or False)#lookup_needs_distinct(self.opts, key))
        except FieldDoesNotExist, e:
            raise IncorrectLookupParameters(e)

        try:
            m_lookup_params = copy.deepcopy(lookup_params) 
            for k,v in lookup_params.items():
                if k.endswith('__in'):
                    m_v = v.split(',')
                    m_lookup_params[k] = m_v
            queryset = queryset.filter(**m_lookup_params)
        except (SuspiciousOperation, ImproperlyConfigured):
            raise
        except Exception, e:
            raise IncorrectLookupParameters(e)

        query = self.request.GET.get(SEARCH_VAR, '')

        # Apply keyword searches.
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        if self.search_fields and query:
            if not self.admin_view.search_sphinx_ins:
                orm_lookups = [construct_search(str(search_field))
                               for search_field in self.search_fields]
                for bit in query.split():
                    or_queries = [models.Q(**{orm_lookup: bit})
                                  for orm_lookup in orm_lookups]
                    queryset = queryset.filter(reduce(operator.or_, or_queries))
                if not use_distinct:
                    for search_spec in orm_lookups:
                        if lookup_needs_distinct(self.opts, search_spec):
                            use_distinct = True
                            break
            self.admin_view.search_query = query

        if 0 and use_distinct:
            return queryset.distinct()
        else:
            return queryset

    # Media
    def get_media(self, media):
        if bool(filter(lambda s: isinstance(s, DateFieldListFilter), self.filter_specs)):
            media = media + self.vendor('datepicker.css', 'datepicker.js',
                                        'xadmin.widget.datetime.js')
        if bool(filter(lambda s: isinstance(s, RelatedFieldSearchFilter), self.filter_specs)):
            media = media + self.vendor(
                'select.js', 'select.css', 'xadmin.widget.select.js')
        return media + self.vendor('xadmin.plugin.filters.js')

    # Block Views
    def block_nav_menu(self, context, nodes):
        if self.has_filters:
            nodes.append(loader.render_to_string('xadmin/blocks/model_list.nav_menu.filters.html', context_instance=context))

    def block_nav_form(self, context, nodes):
        if self.search_fields:
            nodes.append(
                loader.render_to_string(
                    'xadmin/blocks/model_list.nav_form.search_form.html',
                    {'search_var': SEARCH_VAR,
                        'remove_search_url': self.admin_view.get_query_string(remove=[SEARCH_VAR]),
                        'search_form_params': self.admin_view.get_form_params(remove=[SEARCH_VAR,'p'])},
                    context_instance=context))

site.register_plugin(FilterPlugin, ListAdminView)
site.register_plugin(FilterPlugin, GridPage)



# @filter_manager.register
class QuickFilterMultiSelectFieldListFilter(MultiSelectFieldListFilter):
    """ Delegates the filter to the default filter and ors the results of each
     
    Lists the distinct values of each field as a checkbox
    Uses the default spec for each 
     
    """
    template = 'xadmin/filters/quickfilter.html'

class QuickFilterPlugin(BasePlugin):
    """
    Add a filter menu to the left column of the page
    """
    list_quick_filter = () # these must be a subset of list_filter to work
    quickfilter = {} 
    search_fields = ()
    free_query_filter = True
    
    def init_request(self, *args, **kwargs):
        menu_style_accordian = hasattr(self.admin_view,'menu_style') and self.admin_view.menu_style == 'accordion'
        return bool(self.list_quick_filter) and not menu_style_accordian
    
    # Media
    def get_media(self, media):
        return media + self.vendor('xadmin.plugin.quickfilter.js','xadmin.plugin.quickfilter.css')
    
    def lookup_allowed(self, lookup, value):
        model = self.model
        # Check FKey lookups that are allowed, so that popups produced by
        # ForeignKeyRawIdWidget, on the basis of ForeignKey.limit_choices_to,
        # are allowed to work.
        for l in model._meta.related_fkey_lookups:
            for k, v in widgets.url_params_from_lookup_dict(l).items():
                if k == lookup and v == value:
                    return True
 
        parts = lookup.split(LOOKUP_SEP)
 
        # Last term in lookup is a query term (__exact, __startswith etc)
        # This term can be ignored.
        if len(parts) > 1 and parts[-1] in QUERY_TERMS:
            parts.pop()
 
        # Special case -- foo__id__exact and foo__id queries are implied
        # if foo has been specificially included in the lookup list; so
        # drop __id if it is the last part. However, first we need to find
        # the pk attribute name.
        rel_name = None
        for part in parts[:-1]:
            try:
                field, _, _, _ = model._meta.get_field_by_name(part)
            except FieldDoesNotExist:
                # Lookups on non-existants fields are ok, since they're ignored
                # later.
                return True
            if hasattr(field, 'rel'):
                model = field.rel.to
                rel_name = field.rel.get_related_field().name
            elif isinstance(field, RelatedObject):
                model = field.model
                rel_name = model._meta.pk.name
            else:
                rel_name = None
        if rel_name and len(parts) > 1 and parts[-1] == rel_name:
            parts.pop()
 
        if len(parts) == 1:
            return True
        clean_lookup = LOOKUP_SEP.join(parts)
        return clean_lookup in self.list_quick_filter
 
    def get_list_queryset(self, queryset):
        lookup_params = dict([(smart_str(k)[len(FILTER_PREFIX):], v) for k, v in self.admin_view.params.items() if smart_str(k).startswith(FILTER_PREFIX) and v != ''])
        for p_key, p_val in lookup_params.iteritems():
            if p_val == "False":
                lookup_params[p_key] = False
        use_distinct = False
        
        if not hasattr(self.admin_view,'quickfilter'):
            self.admin_view.quickfilter = {}
 
        # for clean filters
        self.admin_view.quickfilter['has_query_param'] = bool(lookup_params)
        self.admin_view.quickfilter['clean_query_url'] = self.admin_view.get_query_string(remove=[k for k in self.request.GET.keys() if k.startswith(FILTER_PREFIX)])
 
        # Normalize the types of keys
        if not self.free_query_filter:
            for key, value in lookup_params.items():
                if not self.lookup_allowed(key, value):
                    raise SuspiciousOperation("Filtering by %s not allowed" % key)
 
        self.filter_specs = []
        if self.list_quick_filter:
            for list_quick_filter in self.list_quick_filter:
                field_path = None
                field_order_by = None
                field_limit = None
                field_parts = []
                sort_key = None 
                cache_config = None
                
                if type(list_quick_filter)==dict and 'field' in list_quick_filter:
                    field = list_quick_filter['field']
                    if 'order_by' in list_quick_filter:
                        field_order_by = list_quick_filter['order_by']
                    if 'limit' in list_quick_filter:
                        field_limit = list_quick_filter['limit']
                    if 'sort' in list_quick_filter and callable(list_quick_filter['sort']):
                        sort_key = list_quick_filter['sort']
                    if 'cache' in list_quick_filter and type(list_quick_filter)==dict:
                        cache_config = list_quick_filter['cache']
                        
                else:        
                    field = list_quick_filter # This plugin only uses MultiselectFieldListFilter
                
                if not isinstance(field, models.Field):
                    field_path = field
                    field_parts = get_fields_from_path(self.model, field_path)
                    field = field_parts[-1]
                spec = QuickFilterMultiSelectFieldListFilter(field, self.request, lookup_params,self.model, self.admin_view, field_path=field_path,field_order_by=field_order_by,field_limit=field_limit,sort_key=sort_key,cache_config=cache_config)
                 
                if len(field_parts)>1:
                    spec.title = "%s %s"%(field_parts[-2].name,spec.title) 
                 
                # Check if we need to use distinct()
                use_distinct = True#(use_distinct orlookup_needs_distinct(self.opts, field_path))
                if spec and spec.has_output():
                    try:
                        new_qs = spec.do_filte(queryset)
                    except ValidationError, e:
                        new_qs = None
                        self.admin_view.message_user(u"<b>过滤器错误:</b> %s" % e.messages[0], 'error')
                    if new_qs is not None:
                        queryset = new_qs
 
                    self.filter_specs.append(spec)
 
        self.has_filters = bool(self.filter_specs)
        self.admin_view.quickfilter['filter_specs'] = self.filter_specs
        self.admin_view.quickfilter['used_filter_num'] = len(filter(lambda f: f.is_used, self.filter_specs))
 
        if use_distinct:
            return queryset.distinct()
        else:
            return queryset
    
    def block_left_navbar(self, context, nodes):
        nodes.append(loader.render_to_string('xadmin/blocks/modal_list.left_navbar.quickfilter.html',context))
        
site.register_plugin(QuickFilterPlugin, ListAdminView)