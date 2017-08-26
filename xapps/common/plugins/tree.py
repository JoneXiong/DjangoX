#coding:utf-8
from collections import Iterable

import xadmin
from django import forms
from django.db.models import ManyToManyField, ForeignKey
#from django.forms.util import flatatt
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from xadmin.views import BasePlugin, ModelFormAdminView
from xadmin import dutils

class TreeSelect(object):

    def fill_output(self, output, choices, str_values, label_list):
        if len(choices):
            output.append(u'<ul>')
            for (option_value, option_label, children) in choices:
                option_value = force_unicode(option_value)
                option_label = conditional_escape(force_unicode(option_label))

                children_output = []
                self.fill_output(children_output, children, str_values, label_list)

                classes = []
                if children_output:
                    classes.append('jstree-open')
                if option_value in str_values:
                    classes.append('jstree-checked')
                    label_list.append(option_label)

                output.append(u'<li value="%s" label="%s" class="%s"><a href="javascript:void(0);">%s</a>' % \
                    (option_value, option_label, " ".join(classes), option_label))
                if children_output:
                    output.extend(children_output)
                output.append(u'</li>')

            output.append(u'</ul>')

    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        if self.base_css=='admin-fk-tree-leaf':
            _base_css = "admin-fk-tree leaf"
        else:
            _base_css = self.base_css
        if attrs:
            attrs['class'] = attrs.get('class', '') + ' %s open'%_base_css
        else:
            attrs['class'] = '%s open'%_base_css

        final_attrs = self.build_attrs(attrs, name=name)
        label_list = []
        output = [u'<div class="dropdown-menu jstree-container"><input type="search" placeholder="Search" id="jstree-search"></input><div%s role="combobox">' % dutils.flatatt(final_attrs)]
        # Normalize to strings
        if self.base_css=='admin-m2m-tree':
            str_values = set([force_unicode(v) for v in value])
        else:
            if value:
                str_values = [force_unicode(value)]
            else:
                str_values = []
        self.fill_output(output, self.choices, str_values, label_list)
        raw_str = ''
        if self.base_css in ['admin-fk-tree', 'admin-fk-tree-leaf']:
            raw_str = '<input type="hidden" id="id_%s" name="%s" value="%s"></input>'%(name, name,str_values and str_values.pop() or '')
        output.append(u'</div></div>')

        wapper = '''
<div class="dropdown">%s
<button type="button" class="btn dropdown-toggle btn-default bs-placeholder" data-toggle="dropdown" role="button" title="点击下拉选择" aria-expanded="true"><span class="filter-option pull-left">%s</span>&nbsp;<span class="bs-caret"><span class="caret"></span></span></button>
        '''%(raw_str, (', '.join(label_list) or '请选择...'))
        output.insert(0, wapper)
        output.append(u'</div>')

        return mark_safe(u'\n'.join(output))

class TreeCheckboxSelect(TreeSelect, forms.CheckboxSelectMultiple):
    base_css = 'admin-m2m-tree'
    pass

class TreeRadioSelect(TreeSelect, forms.RadioSelect):
    base_css = 'admin-fk-tree'
    pass

class TreeRadioSelectLeaf(TreeSelect, forms.RadioSelect):
    base_css = 'admin-fk-tree-leaf'
    pass

class ModelTreeIterator(object):

    def __init__(self, field, parent=None):
        self.field = field
        self.queryset = field.queryset.filter(**{field.parent_field: parent})

    def __iter__(self):
        #if self.field.empty_label is not None:
        #    yield (u"", self.field.empty_label)
        if hasattr(self.field, 'cache_choices'):
            if self.field.choice_cache is None:
                self.field.choice_cache = [
                    self.choice(obj) for obj in self.queryset.all()
                ]
                yield choice
        else:
            for obj in self.queryset.all():
                yield self.choice(obj)

    def __len__(self):
        return len(self.queryset)

    def choice(self, obj):
        return (self.field.prepare_value(obj), self.field.label_from_instance(obj), ModelTreeIterator(self.field, obj))


class ModelTreeChoiceField(forms.ModelMultipleChoiceField):
    widget = TreeCheckboxSelect
    parent_field = 'parent'

    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices
        return ModelTreeIterator(self)
    choices = property(_get_choices, forms.ChoiceField._set_choices)

class ModelTreeChoiceFieldFK(forms.ModelChoiceField):
    widget = TreeRadioSelect
    parent_field = 'parent'

    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices
        return ModelTreeIterator(self)
    choices = property(_get_choices, forms.ChoiceField._set_choices)

class ModelTreeChoiceFieldFKLeaf(ModelTreeChoiceFieldFK):
    widget = TreeRadioSelectLeaf

class M2MTreePlugin(BasePlugin):

    def init_request(self, *args, **kwargs):
        self.include_m2m_tree = False
        return hasattr(self.admin_view, 'style_fields') and \
            ('m2m_tree' in self.admin_view.style_fields.values() or 'fk_tree' in self.admin_view.style_fields.values() or 'fk_tree_leaf' in self.admin_view.style_fields.values())

    def get_field_style(self, attrs, db_field, style, **kwargs):
        if style == 'm2m_tree' and isinstance(db_field, ManyToManyField):
            self.include_m2m_tree = True
            return {'form_class': ModelTreeChoiceField, 'help_text': None}
        if style == 'fk_tree' and isinstance(db_field, ForeignKey):
            self.include_m2m_tree = True
            return {'form_class': ModelTreeChoiceFieldFK, 'help_text': None}
        if style == 'fk_tree_leaf' and isinstance(db_field, ForeignKey):
            self.include_m2m_tree = True
            return {'form_class': ModelTreeChoiceFieldFKLeaf, 'help_text': None}
        return attrs

    def get_media(self, media):
        if self.include_m2m_tree:
            media.add_js([self.static('common/js/jquery.jstree.js'), self.static('common/js/form_tree.js')])
        return media

xadmin.site.register_plugin(M2MTreePlugin, ModelFormAdminView)
