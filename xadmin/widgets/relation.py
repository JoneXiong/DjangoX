# coding=utf-8
import json
from itertools import chain

from django import forms
from django.utils.html import escape, format_html,conditional_escape
from django.utils.text import Truncator
from django.contrib.admin.templatetags.admin_static import static
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.utils import six
from django.utils import formats
from django.utils.encoding import force_text,force_unicode
from django.template import loader

from xadmin import dutils
from ..util import vendor
from .. import defs

def url_params_from_lookup_dict(lookups):
    """
    Converts the type of lookups specified in a ForeignKey limit_choices_to
    attribute to a dictionary of query parameters
    """
    params = {}
    if lookups and hasattr(lookups, 'items'):
        items = []
        for k, v in lookups.items():
            if isinstance(v, (tuple, list)):
                v = ','.join([str(x) for x in v])
            elif isinstance(v, bool):
                # See django.db.fields.BooleanField.get_prep_lookup
                v = ('0', '1')[v]
            else:
                v = six.text_type(v)
            items.append((k, v))
        params.update(dict(items))
    return params


class ForeignKeySearchWidget(forms.TextInput):
    u'''select2下拉选择, ajax请求数据'''
    def __init__(self, rel, admin_view, attrs=None, using=None):
        self.rel = rel
        self.admin_view = admin_view
        self.db = using
        super(ForeignKeySearchWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        to_opts = self.rel.to._meta
        if attrs is None:
            attrs = {}
        if "class" not in attrs:
            attrs['class'] = 'select-search'
        else:
            attrs['class'] = attrs['class'] + ' select-search'
        attrs['data-search-url'] = self.admin_view.get_admin_url(
            '%s_%s_changelist' % (to_opts.app_label, to_opts.module_name))
        attrs['data-placeholder'] = _('Search %s') % to_opts.verbose_name
        attrs['data-choices'] = '?'
        if self.rel.limit_choices_to:
            for i in list(self.rel.limit_choices_to):
                attrs['data-choices'] += "&_p_%s=%s" % (i, self.rel.limit_choices_to[i])
            attrs['data-choices'] = format_html(attrs['data-choices'])
        if value:
            attrs['data-label'] = self.label_for_value(value)

        return super(ForeignKeySearchWidget, self).render(name, value, attrs)

    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        try:
            obj = self.rel.to._default_manager.using(
                self.db).get(**{key: value})
            return '%s' % escape(Truncator(obj).words(14, truncate='...'))
        except (ValueError, self.rel.to.DoesNotExist):
            return ""

    @property
    def media(self):
        return vendor('select.js', 'select.css', 'xadmin.widget.select.js')
    
    
class RawIdWidget(forms.TextInput):
    
    label_format = '<input type="text" id="id_%s_show" class="form-control" value="%s" readonly="readonly" />'
    
    def render(self, name, value, attrs=None):
        to_opts = self.r_model._meta
        
        if attrs is None:
            attrs = {}
        extra = []
        if 1:#self.r_model in self.admin_view.admin_site._registry:
            from xadmin.views.page import GridPage
            if issubclass(self.r_model, GridPage):
                related_url = self.r_model.get_page_url()
            else:
                related_url = self.admin_view.get_admin_url(
                    '%s_%s_changelist' % (to_opts.app_label, to_opts.module_name))

            params = self.url_parameters(name)
            if params:
                url = '?' + '&amp;'.join(['%s=%s' % (k, v) for k, v in params.items()])
            else:
                url = ''
            if "class" not in attrs:
                attrs['class'] = 'vForeignKeyRawIdAdminField' # The JavaScript code looks for this hook.

            if value:
                if attrs['class'] == 'vManyToManyRawIdAdminField':
                    self.label_format = '<div class="obj-show " id="id_%s_show">%s</div>'
                input_html = self.label_for_value(value, name=name)
            else:
                if attrs['class'] == 'vManyToManyRawIdAdminField':
                    input_html = '<div class="obj-show " id="id_%s_show"></div>'%name
                else:
                    input_html = '<input type="text" id="id_%s_show" class="form-control" value="" readonly="readonly" />'%name
            _css = attrs['class'] == 'vManyToManyRawIdAdminField' and 'm2m-field' or 'fk-field'
            all_html = '''
            <div class="input-group %s">
                %s
                <span class="input-group-btn vertical-top">
                    <a href="%s%s" class="btn btn-primary related-lookup" id="lookup_id_%s" onclick="return showRelatedObjectLookupPopup(this);"><i class="fa fa-search"></i></a>
                    <a href="javascript://" class="btn btn-default related-lookup" id="remove_id_%s"  onclick="return removeRelatedObject(this);" ><i class="fa fa-remove"></i></a>
                </span>
            </div>
            '''%(_css, input_html, related_url, url, name, name)
            extra.append(all_html)

        attrs['type'] = 'hidden'
        output = [super(RawIdWidget, self).render(name, value, attrs)] + extra

        return mark_safe(''.join(output))
    
    def _render_label(self, name, value):
        return self.label_format %(name, escape(Truncator(value).words(14, truncate='...')) )
    
    @property
    def media(self):
        return vendor('xadmin.widget.RelatedObjectLookups.js','xadmin.widget.select-related.css')


class ForeignKeyRawIdWidget(RawIdWidget):
    """
    打开Window窗口选择对象将id, title带过来 (单选)
    """
    def __init__(self, rel, admin_view, attrs=None, using=None):
        self.rel = rel
        self.r_model = rel.to
        
        self.admin_view = admin_view
        self.db = using
        super(ForeignKeyRawIdWidget, self).__init__(attrs)

    def base_url_parameters(self):
        return url_params_from_lookup_dict(self.rel.limit_choices_to)

    def url_parameters(self,name=None):
        params = self.base_url_parameters()
        if hasattr(self.admin_view, 'fk_url_param'):
            m_param = self.admin_view.fk_url_param
            if name in m_param.keys():
                params.update(m_param[name])
        params.update({defs.TO_FIELD_VAR: self.rel.get_related_field().name})
        return params

    def label_for_value(self, value, name=None):
        key = self.rel.get_related_field().name
        try:
            obj = self.r_model._default_manager.using(self.db).get(**{key: value})
            return self._render_label(name, obj)
        except (ValueError, self.r_model.DoesNotExist):
            return ''
    
    
class ManyToManyRawIdWidget(ForeignKeyRawIdWidget):
    """
    打开Window窗口选择对象将id, title带过来 (多选)
    """
    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        attrs['class'] = 'vManyToManyRawIdAdminField'
        if type(value) in (list,tuple):
            value = ','.join([force_text(v) for v in value])
        return super(ManyToManyRawIdWidget, self).render(name, value, attrs)

    def label_for_value(self, value, name=None):
        m_value = value.split(',')
        m_value = [e for e in m_value if e]
        key = self.rel.get_related_field().name
        objs = objs = self.rel.to._default_manager.using(self.db).filter(**{key+'__in': m_value})
        li_format = '''<a class="btn btn-sm" onclick="removeSingleObject(this,'%s', '%s');">%s</a>'''
        tar_list = ''
        for obj in objs:
            show_val = escape(Truncator(obj).words(14, truncate='...'))
            val = getattr(obj, key)
            tar_list += li_format%( 'id_'+name, val, show_val)
        return self.label_format %(name, tar_list )

    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        if value:
            return value.split(',')

    def _has_changed(self, initial, data):
        if initial is None:
            initial = []
        if data is None:
            data = []
        if len(initial) != len(data):
            return True
        for pk1, pk2 in zip(initial, data):
            if force_text(pk1) != force_text(pk2):
                return True
        return False
    
    
class ForeignKeyPopupWidget(RawIdWidget):
    """
    打开div窗口 选择对象 设置id, title (单选)
    """
    def __init__(self, admin_view, r_model, t_name, s_name=None, attrs=None, using=None):
        self.r_model = r_model
        self.t_name = t_name
        self.s_name = s_name
        
        self.admin_view = admin_view
        self.db = using
        super(ForeignKeyPopupWidget, self).__init__(attrs)

    def url_parameters(self,name=None):
        params = {}
        if hasattr(self.admin_view, 'fk_url_param'):
            m_param = self.admin_view.fk_url_param
            if name in m_param.keys():
                params.update(m_param[name])
        params[defs.TO_FIELD_VAR] = self.t_name
        if self.s_name:
            params[defs.SHOW_FIELD_VAR] = self.s_name
        return params

    def label_for_value(self, value, name=None):
        key = self.t_name
        from xadmin.views.page import GridPage
        if issubclass(self.r_model, GridPage):
            return self._render_label( name, self.r_model.queryset_class().verbose(value) )
        else:
            try:
                obj = self.r_model._default_manager.using(self.db).get(**{key: value})
                if self.s_name:
                    show_val = getattr(obj, self.s_name)
                    if callable(show_val):show_val = show_val()
                else:
                    show_val = obj
                return self._render_label(name, show_val)
            except (ValueError, self.r_model.DoesNotExist):
                return self._render_label(name, '')
        

class ManyToManyPopupWidget(ForeignKeyPopupWidget):
    """
    打开div窗口 选择对象 设置id, title (多选)
    """
    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        attrs['class'] = 'vManyToManyRawIdAdminField'
        if type(value) in (list,tuple):
            value = ','.join([force_text(v) for v in value])
        return super(ManyToManyPopupWidget, self).render(name, value, attrs)
    
    def label_for_value(self, value, name=None):
        m_value = value.split(',')
        m_value = [e for e in m_value if e]
        key = self.t_name
        objs = self.r_model._default_manager.using(self.db).filter(**{key+'__in': m_value})
        li_format = '''<a class="btn btn-sm" onclick="removeSingleObject(this,'%s', '%s');">%s</a>'''
        tar_list = ''
        for obj in objs:
            if self.s_name:
                show_val = getattr(obj, self.s_name)
                if callable(show_val):show_val = show_val()
                show_val = escape(Truncator(show_val).words(14, truncate='...'))
            else:
                show_val = escape(Truncator(obj).words(14, truncate='...'))
            val = getattr(obj, key)
            tar_list += li_format%( 'id_'+name, val, show_val)
        return self.label_format %(name, tar_list )

    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        return value

    
class SelectMultipleTransfer(forms.SelectMultiple):
    """
    左右转移选择控件 (多选)
    """
    @property
    def media(self):
        return vendor('xadmin.widget.select-transfer.js', 'xadmin.widget.select-transfer.css')

    def __init__(self, verbose_name, is_stacked, attrs=None, choices=()):
        self.verbose_name = verbose_name
        self.is_stacked = is_stacked
        super(SelectMultipleTransfer, self).__init__(attrs, choices)

    def render_opt(self, selected_choices, option_value, option_label):
        option_value = force_unicode(option_value)
        return u'<option value="%s">%s</option>' % (
            escape(option_value), conditional_escape(force_unicode(option_label))), bool(option_value in selected_choices)

    def render(self, name, value, attrs=None, choices=()):
        if attrs is None:
            attrs = {}
        attrs['class'] = ''
        if self.is_stacked:
            attrs['class'] += 'stacked'
        if value is None:
            value = []
        final_attrs = self.build_attrs(attrs, name=name)

        selected_choices = set(force_unicode(v) for v in value)
        available_output = []
        chosen_output = []

        for option_value, option_label in chain(self.choices, choices):
            if isinstance(option_label, (list, tuple)):
                available_output.append(u'<optgroup label="%s">' %
                                        escape(force_unicode(option_value)))
                for option in option_label:
                    output, selected = self.render_opt(
                        selected_choices, *option)
                    if selected:
                        chosen_output.append(output)
                    else:
                        available_output.append(output)
                available_output.append(u'</optgroup>')
            else:
                output, selected = self.render_opt(
                    selected_choices, option_value, option_label)
                if selected:
                    chosen_output.append(output)
                else:
                    available_output.append(output)

        context = {
            'verbose_name': self.verbose_name,
            'attrs': attrs,
            'field_id': attrs['id'],
            'flatatts': dutils.flatatt(final_attrs),
            'available_options': u'\n'.join(available_output),
            'chosen_options': u'\n'.join(chosen_output),
        }
        return mark_safe(loader.render_to_string('xadmin/forms/transfer.html', context))
    
    
class SelectMultipleDropdown(forms.SelectMultiple):
    """
    下拉勾选控件 (多选)
    """
    @property
    def media(self):
        return vendor('multiselect.js', 'multiselect.css', 'xadmin.widget.multiselect.js')

    def render(self, name, value, attrs=None, choices=()):
        if attrs is None:
            attrs = {}
        attrs['class'] = 'selectmultiple selectdropdown'
        return super(SelectMultipleDropdown, self).render(name, value, attrs, choices)
    
    
class SelectMultipleDropselect(forms.SelectMultiple):
    """
    select2下拉选择控件 同步加载所有数据 (多选)
    """
    @property
    def media(self):
        return vendor('select.js', 'select.css', 'xadmin.widget.select.js')

    def render(self, name, value, attrs=None, choices=()):
        if attrs is None:
            attrs = {}
        attrs['class'] = 'select2dropdown'
        attrs['multiple'] = 'multiple'
        return super(SelectMultipleDropselect, self).render(name, value, attrs, choices)
    
    
class SelectMultipleAjax(forms.SelectMultiple):
    """
    select2下拉选择控件 异步加载 (单选/多选)
    """
    def __init__(self, rel, admin_view, multiple, attrs=None):
        self.rel = rel
        self.admin_view = admin_view
        self.multiple = multiple
        super(SelectMultipleAjax, self).__init__(attrs)
        
    def value_from_datadict(self, data, files, name):
        m_data = data.get(name, None)
        if m_data:
            m_list = m_data.split(',')
            return [int(k) for k in m_list if k]
        else:
            return []
        
    def _format_value(self, value):
        if self.is_localized:
            return formats.localize_input(value)
        value = [str(e) for e in value]
        return ','.join(value)
    
    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        q_dict = {}
        q_dict[key+'__in'] = value
        objs = self.rel.to._default_manager.filter(**q_dict)
        if self.multiple:
            return json.dumps( [{'id': e.pk, '__str__': escape(Truncator(e).words(14, truncate='...')) } for e in objs] )
        else:
            if objs:
                obj = objs[0]
                return json.dumps( {'id': obj.pk, '__str__': escape(Truncator(obj).words(14, truncate='...')) } )
            else:
                return ''

    @property
    def media(self):
        return vendor('select.js', 'select.css', 'xadmin.widget.select.js')

    def render(self, name, value, attrs=None, choices=()):
        
        
        to_opts = self.rel.to._meta
        if attrs is None:
            attrs = {}
        attrs['class'] = 'select2ajax'
        if self.multiple:
            attrs['multiple'] = 'multiple'
        attrs['data-search-url'] = self.admin_view.get_admin_url(
            '%s_%s_changelist' % (to_opts.app_label, to_opts.module_name))
        attrs['data-placeholder'] = _('Search %s') % to_opts.verbose_name
        attrs['data-choices'] = '?'
        if self.rel.limit_choices_to:
            for i in list(self.rel.limit_choices_to):
                attrs['data-choices'] += "&_p_%s=%s" % (i, self.rel.limit_choices_to[i])
            attrs['data-choices'] = format_html(attrs['data-choices'])
        if value:
            attrs['data-label'] = self.label_for_value(value)
            
            
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type='text', name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_text(self._format_value(value))
        return format_html('<input{0} />', flatatt(final_attrs))
