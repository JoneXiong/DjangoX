#coding:utf-8
import xadmin
from django import forms
from django.db.models import ManyToManyField
#from django.forms.util import flatatt
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from xadmin.views import BasePlugin, ModelFormAdminView
from xadmin import dutils

class TreeCheckboxSelect(forms.CheckboxSelectMultiple):

    def fill_output(self, output, choices, str_values):
        if len(choices):
            output.append(u'<ul>')
            for (option_value, option_label, children) in choices:
                option_value = force_unicode(option_value)
                option_label = conditional_escape(force_unicode(option_label))

                children_output = []
                self.fill_output(children_output, children, str_values)

                classes = []
                if children_output:
                    classes.append('jstree-open')
                if option_value in str_values:
                    classes.append('jstree-checked')

                output.append(u'<li value="%s" class="%s"><a href="javascript:void(0);">%s</a>' % \
                    (option_value, " ".join(classes), option_label))
                if children_output:
                    output.extend(children_output)
                output.append(u'</li>')
                
            output.append(u'</ul>')

    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        if attrs:
            attrs['class'] = attrs.get('class', '') + ' admin-tree'
        else:
            attrs['class'] = 'admin-tree'

        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<div%s>' % dutils.flatatt(final_attrs)]
        # Normalize to strings
        str_values = set([force_unicode(v) for v in value])
        self.fill_output(output, self.choices, str_values)
        output.append(u'</div>')
        return mark_safe(u'\n'.join(output))

class ModelTreeIterator(object):

    def __init__(self, field, parent=None):
        self.field = field
        self.queryset = field.queryset.filter(**{field.parent_field: parent})

    def __iter__(self):
        if self.field.empty_label is not None:
            yield (u"", self.field.empty_label)
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

class M2MTreePlugin(BasePlugin):

    def init_request(self, *args, **kwargs):
        self.include_m2m_tree = False
        return hasattr(self.admin_view, 'style_fields') and \
            'm2m_tree' in self.admin_view.style_fields.values()

    def get_field_style(self, attrs, db_field, style, **kwargs):
        if style == 'm2m_tree' and isinstance(db_field, ManyToManyField):
            self.include_m2m_tree = True
            return {'form_class': ModelTreeChoiceField, 'help_text': None}
        return attrs

    def get_media(self, media):
        if self.include_m2m_tree:
            media.add_js([self.static('common/js/jquery.jstree.js'), self.static('common/js/form_tree.js')])
        return media

xadmin.site.register_plugin(M2MTreePlugin, ModelFormAdminView)
