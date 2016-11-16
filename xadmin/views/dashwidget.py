# coding=utf-8

from django import forms
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse, NoReverseMatch
from django.db.models.base import ModelBase
from django.template import loader
from django.template.context import RequestContext
from django.test.client import RequestFactory
from django.utils.encoding import force_unicode, smart_unicode
from django.utils.translation import ugettext as _
from django.utils.http import urlencode, urlquote

from xadmin import widgets as exwidgets
from xadmin.layout import FormHelper
from xadmin.models import UserWidget
from xadmin.views.edit import CreateAdminView
from xadmin.views.list import ListAdminView
from xadmin import dutils


class ModelChoiceIterator(object):
    '''
    注册模型迭代器
    '''
    def __init__(self, field):
        self.field = field

    def __iter__(self):
        from xadmin import site as g_admin_site
        for m, ma in g_admin_site._registry.items():
            yield ('%s.%s' % (m._meta.app_label, m._meta.module_name),
                   m._meta.verbose_name)


class ModelChoiceField(forms.ChoiceField):
    '''
    模型选择表单字段
    '''

    def __init__(self, required=True, widget=None, label=None, initial=None,
                 help_text=None, *args, **kwargs):
        # Call Field instead of ChoiceField __init__() because we don't need
        # ChoiceField.__init__().
        forms.Field.__init__(self, required, widget, label, initial, help_text,
                             *args, **kwargs)
        self.widget.choices = self.choices

    def __deepcopy__(self, memo):
        result = forms.Field.__deepcopy__(self, memo)
        return result

    def _get_choices(self):
        return ModelChoiceIterator(self)

    choices = property(_get_choices, forms.ChoiceField._set_choices)

    def to_python(self, value):
        if isinstance(value, ModelBase):
            return value
        app_label, model_name = value.lower().split('.')
        return dutils.get_model(app_label, model_name)

    def prepare_value(self, value):
        if isinstance(value, ModelBase):
            value = '%s.%s' % (value._meta.app_label, value._meta.module_name)
        return value

    def valid_value(self, value):
        value = self.prepare_value(value)
        for k, v in self.choices:
            if value == smart_unicode(k):
                return True
        return False


class WidgetManager(object):
    _widgets = None

    def __init__(self):
        self._widgets = {}

    def register(self, widget_class):
        self._widgets[widget_class.widget_type] = widget_class
        return widget_class

    def get(self, name):
        return self._widgets[name]

    def get_widgets(self, page_id):
        return self._widgets.values()

widget_manager = WidgetManager()


class WidgetDataError(Exception):

    def __init__(self, widget, errors):
        super(WidgetDataError, self).__init__(str(errors))
        self.widget = widget
        self.errors = errors


class BaseWidget(forms.Form):

    template = 'xadmin/widgets/base.html'
    description = 'Base Widget, don\'t use it.'
    widget_title = None
    widget_icon = 'fa fa-plus-square'
    widget_type = 'base'
    base_title = None

    id = forms.IntegerField(label=_('Widget ID'), widget=forms.HiddenInput)
    title = forms.CharField(label=_('Widget Title'), required=False, widget=exwidgets.AdminTextInputWidget)

    def __init__(self, dashboard, data):
        self.dashboard = dashboard
        self.admin_site = dashboard.admin_site
        self.request = dashboard.request
        self.user = dashboard.request.user
        self.convert(data)
        super(BaseWidget, self).__init__(data)

        if not self.is_valid():
            raise WidgetDataError(self, self.errors.as_text())

        self.setup()

    def setup(self):
        helper = FormHelper()
        helper.form_tag = False
        self.helper = helper

        self.id = self.cleaned_data['id']
        self.title = self.cleaned_data['title'] or self.base_title

        if not (self.user.is_superuser or self.has_perm()):
            raise PermissionDenied

    @property
    def widget(self):
        context = {'widget_id': self.id, 'widget_title': self.title, 'widget_icon': self.widget_icon,
            'widget_type': self.widget_type, 'form': self, 'widget': self}
        self.context(context)
        return loader.render_to_string(self.template, context, context_instance=RequestContext(self.request))

    def context(self, context):
        pass

    def convert(self, data):
        pass

    def has_perm(self):
        return False

    def save(self):
        value = dict([(f.name, f.value()) for f in self])
        user_widget = UserWidget.objects.get(id=self.id)
        user_widget.set_value(value)
        user_widget.save()

    def static(self, path):
        return self.dashboard.static(path)

    def vendor(self, *tags):
        return self.dashboard.vendor(*tags)

    def media(self):
        return forms.Media()


@widget_manager.register
class HtmlWidget(BaseWidget):
    widget_type = 'html'
    widget_icon = 'fa fa-file-o'
    description = _(
        u'Html Content Widget, can write any html content in widget.')

    content = forms.CharField(label=_(
        'Html Content'), widget=exwidgets.AdminTextareaWidget, required=False)

    def has_perm(self):
        return True

    def context(self, context):
        context['content'] = self.cleaned_data['content']
        
        
class ModelBaseWidget(BaseWidget):

    app_label = None
    module_name = None
    model_perm = 'change'
    model = ModelChoiceField(label=_(u'Target Model'), widget=exwidgets.SelectWidget)

    def __init__(self, dashboard, data):
        self.dashboard = dashboard
        super(ModelBaseWidget, self).__init__(dashboard, data)

    def setup(self):
        self.model = self.cleaned_data['model']
        self.app_label = self.model._meta.app_label
        self.module_name = self.model._meta.module_name

        super(ModelBaseWidget, self).setup()

    def has_perm(self):
        return self.dashboard.has_model_perm(self.model, self.model_perm)

    def filte_choices_model(self, model, modeladmin):
        return self.dashboard.has_model_perm(model, self.model_perm)

    def model_admin_url(self, name, *args, **kwargs):
        return reverse(
            "%s:%s_%s_%s" % (self.admin_site.app_name, self.app_label,
            self.module_name, name), args=args, kwargs=kwargs)


class PartialBaseWidget(BaseWidget):

    def get_view_class(self, view_class, model=None, **opts):
        admin_class = self.admin_site._registry.get(model) if model else None
        return self.admin_site.get_view_class(view_class, admin_class, **opts)

    def get_factory(self):
        return RequestFactory()

    def setup_request(self, request):
        request.user = self.user
        request.session = self.request.session
        return request

    def make_get_request(self, path, data={}, **extra):
        req = self.get_factory().get(path, data, **extra)
        return self.setup_request(req)

    def make_post_request(self, path, data={}, **extra):
        req = self.get_factory().post(path, data, **extra)
        return self.setup_request(req)
    
    
@widget_manager.register
class QuickBtnWidget(BaseWidget):
    widget_type = 'qbutton'
    description = _(u'Quick button Widget, quickly open any page.')
    template = "xadmin/widgets/qbutton.html"
    base_title = _(u"Quick Buttons")
    widget_icon = 'fa fa-caret-square-o-right'

    def convert(self, data):
        self.q_btns = data.pop('btns', [])

    def get_model(self, model_or_label):
        if isinstance(model_or_label, ModelBase):
            return model_or_label
        else:
            return dutils.get_model(*model_or_label.lower().split('.'))

    def context(self, context):
        btns = []
        for b in self.q_btns:
            btn = {}
            if 'model' in b:
                model = self.get_model(b['model'])
                if not self.user.has_perm("%s.view_%s" % (model._meta.app_label, model._meta.module_name)):
                    continue
                btn['url'] = reverse("%s:%s_%s_%s" % (self.admin_site.app_name, model._meta.app_label,
                                                      model._meta.module_name, b.get('view', 'changelist')))
                btn['title'] = model._meta.verbose_name
                btn['icon'] = self.dashboard.get_model_icon(model)
            else:
                try:
                    btn['url'] = reverse(b['url'])
                except NoReverseMatch:
                    btn['url'] = b['url']

            if 'title' in b:
                btn['title'] = b['title']
            if 'icon' in b:
                btn['icon'] = b['icon']
            btns.append(btn)

        context.update({'btns': btns})

    def has_perm(self):
        return True


@widget_manager.register
class ListWidget(ModelBaseWidget, PartialBaseWidget):
    widget_type = 'list'
    description = _(u'Any Objects list Widget.')
    template = "xadmin/widgets/list.html"
    model_perm = 'view'
    widget_icon = 'fa fa-align-justify'

    def convert(self, data):
        self.list_params = data.pop('params', {})
        self.list_count = data.pop('count', 10)

    def setup(self):
        super(ListWidget, self).setup()

        if not self.title:
            self.title = self.model._meta.verbose_name_plural

        req = self.make_get_request("", self.list_params)
        self.list_view = self.get_view_class(ListAdminView, self.model)(req)
        if self.list_count:
            self.list_view.list_per_page = self.list_count

    def context(self, context):
        list_view = self.list_view
        list_view.make_result_list()

        base_fields = list_view.base_list_display
        if len(base_fields) > 5:
            base_fields = base_fields[0:5]

        context['result_headers'] = [c for c in list_view.result_headers(
        ).cells if c.field_name in base_fields]
        context['results'] = [[o for i, o in
                               enumerate(filter(lambda c:c.field_name in base_fields, r.cells))]
                              for r in list_view.results()]
        context['result_count'] = list_view.result_count
        context['page_url'] = self.model_admin_url('changelist') + "?" + urlencode(self.list_params)


@widget_manager.register
class AddFormWidget(ModelBaseWidget, PartialBaseWidget):
    widget_type = 'addform'
    description = _(u'Add any model object Widget.')
    template = "xadmin/widgets/addform.html"
    model_perm = 'add'
    widget_icon = 'fa fa-plus'

    def setup(self):
        super(AddFormWidget, self).setup()

        if self.title is None:
            self.title = _('Add %s') % self.model._meta.verbose_name

        req = self.make_get_request("")
        self.add_view = self.get_view_class(
            CreateAdminView, self.model, list_per_page=10)(req)
        self.add_view.instance_forms()

    def context(self, context):
        helper = FormHelper()
        helper.form_tag = False

        context.update({
            'addform': self.add_view.form_obj,
            'addhelper': helper,
            'addurl': self.add_view.model_admin_url('add'),
            'model': self.model
        })

    def media(self):
        return self.add_view.media + self.add_view.form_obj.media + self.vendor('xadmin.plugin.quick-form.js')
