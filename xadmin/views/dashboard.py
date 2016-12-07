# coding=utf-8
import copy

from django import forms
from django.core.exceptions import PermissionDenied
from django.forms.forms import DeclarativeFieldsMetaclass
from django.http import Http404
from django.utils.encoding import force_unicode, smart_unicode
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.utils.http import urlencode, urlquote
from django.views.decorators.cache import never_cache

from xadmin.models import UserSettings, UserWidget
from xadmin.sites import site
from xadmin.views.base import SiteView, filter_hook, csrf_protect_m
from xadmin.views.model_page import ModelAdminView
from xadmin.util import unquote
from xadmin import dutils
from dashwidget import widget_manager, WidgetDataError


class WidgetTypeSelect(forms.Widget):

    def __init__(self, widgets, attrs=None):
        super(WidgetTypeSelect, self).__init__(attrs)
        self._widgets = widgets

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        final_attrs['class'] = 'nav nav-pills nav-stacked'
        output = [u'<ul%s>' % dutils.flatatt(final_attrs)]
        options = self.render_options(force_unicode(value), final_attrs['id'])
        if options:
            output.append(options)
        output.append(u'</ul>')
        output.append('<input type="hidden" id="%s_input" name="%s" value="%s"/>' %
                     (final_attrs['id'], name, force_unicode(value)))
        return mark_safe(u'\n'.join(output))

    def render_option(self, selected_choice, widget, id):
        if widget.widget_type == selected_choice:
            selected_html = u' class="active"'
        else:
            selected_html = ''
        return (u'<li%s><a onclick="' +
                'javascript:$(this).parent().parent().find(\'>li\').removeClass(\'active\');$(this).parent().addClass(\'active\');' +
                '$(\'#%s_input\').attr(\'value\', \'%s\')' % (id, widget.widget_type) +
                '"><h4><i class="%s"></i> %s</h4><p>%s</p></a></li>') % (
                    selected_html,
                    widget.widget_icon,
                    widget.widget_title or widget.widget_type,
                    widget.description)

    def render_options(self, selected_choice, id):
        # Normalize to strings.
        output = []
        for widget in self._widgets:
            output.append(self.render_option(selected_choice, widget, id))
        return u'\n'.join(output)


class UserWidgetAdmin(object):

    model_icon = 'fa fa-dashboard'
    list_display = ('widget_type', 'page_id', 'user')
    list_filter = ['user', 'widget_type', 'page_id']
    list_display_links = ('widget_type',)
    user_fields = ['user']
    #hide_menu = True

    wizard_form_list = (
        (_(u"Widget Type"), ('page_id', 'widget_type')),
        (_(u"Widget Params"), {'callback':
                               "get_widget_params_form", 'convert': "convert_widget_params"})
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'widget_type':
            widgets = widget_manager.get_widgets(self.request.GET.get('page_id', ''))
            form_widget = WidgetTypeSelect(widgets)
            return forms.ChoiceField(choices=[(w.widget_type, w.description) for w in widgets],
                                     widget=form_widget, label=_('Widget Type'))
        if 'page_id' in self.request.GET and db_field.name == 'page_id':
            kwargs['widget'] = forms.HiddenInput
        field = super(
            UserWidgetAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        return field

    def get_widget_params_form(self, wizard):
        data = wizard.get_cleaned_data_for_step(wizard.steps.first)
        widget_type = data['widget_type']
        widget = widget_manager.get(widget_type)
        fields = copy.deepcopy(widget.base_fields)
        if 'id' in fields:
            del fields['id']
        return DeclarativeFieldsMetaclass("WidgetParamsForm", (forms.Form,), fields)

    def convert_widget_params(self, wizard, cleaned_data, form):
        widget = UserWidget()
        value = dict([(f.name, f.value()) for f in form])
        widget.set_value(value)
        cleaned_data['value'] = widget.value
        cleaned_data['user'] = self.user

    def get_list_display(self):
        list_display = super(UserWidgetAdmin, self).get_list_display()
        if not self.user.is_superuser:
            list_display.remove('user')
        return list_display

    def queryset(self):
        if self.user.is_superuser:
            return super(UserWidgetAdmin, self).queryset()
        return UserWidget.objects.filter(user=self.user)

    def update_dashboard(self, obj):
        try:
            portal_pos = UserSettings.objects.get(
                user=obj.user, key="dashboard:%s:pos" % obj.page_id)
        except UserSettings.DoesNotExist:
            return
        pos = [[w for w in col.split(',') if w != str(
            obj.id)] for col in portal_pos.value.split('|')]
        portal_pos.value = '|'.join([','.join(col) for col in pos])
        portal_pos.save()

    def delete_model(self):
        self.update_dashboard(self.obj)
        super(UserWidgetAdmin, self).delete_model()

    def delete_models(self, queryset):
        for obj in queryset:
            self.update_dashboard(obj)
        super(UserWidgetAdmin, self).delete_models(queryset)


site.register(UserWidget, UserWidgetAdmin)


class Dashboard(SiteView):

    widget_customiz = True
    widgets = []
    title = _(u"Dashboard")
    icon = None
    app_label = None
    base_template = 'xadmin/base_site_noleft.html'
    template = 'xadmin/views/dashboard.html'

    def get_page_id(self):
        return self.request.path

    def get_portal_key(self):
        return "dashboard:%s:pos" % self.get_page_id()

    @filter_hook
    def get_widget(self, widget_or_id, data=None):
        '''
        实例化widget
        '''
        try:
            if isinstance(widget_or_id, UserWidget):
                widget = widget_or_id
            else:
                widget = UserWidget.objects.get(user=self.user, page_id=self.get_page_id(), id=widget_or_id)
            wid = widget_manager.get(widget.widget_type)

            class widget_with_perm(wid):
                def context(self, context):
                    super(widget_with_perm, self).context(context)
                    context.update({'has_change_permission': self.request.user.has_perm('xadmin.change_userwidget')})
            wid_instance = widget_with_perm(self, data or widget.get_value())
            return wid_instance
        except UserWidget.DoesNotExist:
            return None

    @filter_hook
    def get_init_widget(self):
        u'''
        初始化获取要显示的 widgets
        注: widget_customiz=True 时才会 save
        '''
        portal = []
        widgets = self.widgets
        for col in widgets:
            portal_col = []
            for opts in col:
                try:
                    widget = UserWidget(user=self.user, page_id=self.get_page_id(), widget_type=opts['type'])
                    widget.set_value(opts)
                    if self.widget_customiz:
                        widget.save()
                    else:
                        widget.id = 0
                    portal_col.append(self.get_widget(widget))
                except (PermissionDenied, WidgetDataError):
                    if self.widget_customiz:
                        widget.delete()
                    continue
            portal.append(portal_col)
        if self.widget_customiz:
            UserSettings(
                user=self.user, key="dashboard:%s:pos" % self.get_page_id(),
                value='|'.join([','.join([str(w.id) for w in col]) for col in portal])).save()

        return portal

    @filter_hook
    def get_widgets(self):
        u'''
        构造要显示的 widgets
        '''
        if self.widget_customiz:
            portal_pos = UserSettings.objects.filter(
                user__id=self.user.id, key=self.get_portal_key())
            if len(portal_pos):
                portal_pos = portal_pos[0].value
                widgets = []

                if portal_pos:
                    user_widgets = dict([(uw.id, uw) for uw in UserWidget.objects.filter(user__id=self.user.id, page_id=self.get_page_id())])
                    for col in portal_pos.split('|'):
                        ws = []
                        for wid in col.split(','):
                            if not wid:continue
                            try:
                                widget = user_widgets.get(int(wid))
                                if widget:
                                    ws.append(self.get_widget(widget))
                            except Exception, e:
                                import logging
                                logging.error(e, exc_info=True)
                        widgets.append(ws)

                return widgets
            else:
                # 查不到则初始化获取
                return self.get_init_widget()
        else:
            # 不允许自定义则每次都初始化获取
            return self.get_init_widget()

    @filter_hook
    def get_title(self):
        return self.title

    @filter_hook
    def get_context(self):
        new_context = {
            'title': self.get_title(),
            'icon': self.icon,
            'portal_key': self.get_portal_key(),
            'columns': [('col-sm-%d' % int(12 / len(self.widgets)), ws) for ws in self.widgets],
            'has_add_widget_permission': self.has_model_perm(UserWidget, 'add') and self.widget_customiz,
            'add_widget_url': self.get_admin_url('%s_%s_add' % (UserWidget._meta.app_label, UserWidget._meta.module_name)) +
            "?user=%s&page_id=%s&_redirect=%s" % (self.user.id, self.get_page_id(), urlquote(self.request.get_full_path()))
        }
        context = super(Dashboard, self).get_context()
        context.update(new_context)
        return context

    @never_cache
    def get(self, request, *args, **kwargs):
        self.widgets = self.get_widgets()
        return self.template_response(self.template, self.get_context())

    @csrf_protect_m
    def post(self, request, *args, **kwargs):
        if 'id' in request.POST:
            widget_id = request.POST['id']
            if request.POST.get('_delete', None) != 'on':
                widget = self.get_widget(widget_id, request.POST.copy())
                widget.save()
            else:
                try:
                    widget = UserWidget.objects.get(
                        user=self.user, page_id=self.get_page_id(), id=widget_id)
                    widget.delete()
                    try:
                        portal_pos = UserSettings.objects.get(user=self.user, key="dashboard:%s:pos" % self.get_page_id())
                        pos = [[w for w in col.split(',') if w != str(
                            widget_id)] for col in portal_pos.value.split('|')]
                        portal_pos.value = '|'.join([','.join(col) for col in pos])
                        portal_pos.save()
                    except Exception:
                        pass
                except UserWidget.DoesNotExist:
                    pass

        return self.get(request)

    @filter_hook
    def get_media(self):
        media = super(Dashboard, self).get_media() + \
            self.vendor('xadmin.page.dashboard.js', 'xadmin.page.dashboard.css')
        if self.widget_customiz:
            media = media + self.vendor('xadmin.plugin.portal.js')
        for ws in self.widgets:
            for widget in ws:
                media = media + widget.media()
        return media


class ModelDashboard(Dashboard, ModelAdminView):

    title = _(u"%s Dashboard")

    def get_page_id(self):
        return 'model:%s/%s' % self.model_info

    @filter_hook
    def get_title(self):
        return self.title % force_unicode(self.obj)

    def init_request(self, object_id, *args, **kwargs):
        self.obj = self.get_object(unquote(object_id))

        if not self.has_view_permission(self.obj):
            raise PermissionDenied

        if self.obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') %
                          {'name': force_unicode(self.opts.verbose_name), 'key': escape(object_id)})

    @filter_hook
    def get_context(self):
        new_context = {
            'has_change_permission': self.has_change_permission(self.obj),
            'object': self.obj,
        }
        context = Dashboard.get_context(self)
        context.update(ModelAdminView.get_context(self))
        context.update(new_context)
        return context

    @never_cache
    def get(self, request, *args, **kwargs):
        self.widgets = self.get_widgets()
        return self.template_response(self.get_template_list('views/model_dashboard.html'), self.get_context())


class AppDashboard(Dashboard):
    title = _(u"%s Dashboard")
    icon = "fa fa-dashboard"
    base_template = 'xadmin/base_site.html'

    def get_page_id(self):
        return 'app:%s' % self.app_label
    
    def get_title(self):
        mod = self.admin_site.app_dict[self.app_label]
        return self.title % force_unicode(getattr(mod, 'verbose_name', self.app_label))
    
    def set_widgets(self, context):
        # 设置 self.widgets 
        nav_menu = context['nav_menu']
        widgets = [
            [ ],
            [ ]
        ]
        flag=False
        for item in nav_menu:
            widget = {"type": "qbutton", "title": item['title'], "btns": [] }
            for sitem in item['menus']:
                widget['btns'].append( {'title': sitem['title'], 'url': sitem['url'], 'icon': sitem['icon'] } )
            widgets[int(flag)].append(widget)
            flag = not flag
        self.widgets = widgets
    
    @filter_hook
    def get_context(self):
        context = super(Dashboard, self).get_context()
        self.set_widgets(context)
        self.widgets = self.get_widgets()
        new_context = {
            'title': self.get_title(),
            'icon': self.icon,
            'portal_key': self.get_portal_key(),
            'columns': [('col-sm-%d' % int(12 / len(self.widgets)), ws) for ws in self.widgets],
            'has_add_widget_permission': self.has_model_perm(UserWidget, 'add') and self.widget_customiz,
            'add_widget_url': self.get_admin_url('%s_%s_add' % (UserWidget._meta.app_label, UserWidget._meta.module_name)) +
            "?user=%s&page_id=%s&_redirect=%s" % (self.user.id, self.get_page_id(), urlquote(self.request.get_full_path()))
        }
        context.update(new_context)
        return context

    @never_cache
    def get(self, request, *args, **kwargs):
        return self.template_response(self.template, self.get_context())
