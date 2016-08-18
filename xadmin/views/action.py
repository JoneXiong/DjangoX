# coding=utf-8
import copy

from django import forms
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
from django.http import HttpResponse

from base import filter_hook
from model_page import ModelAdminView
from xadmin.layout import FormHelper, Layout, Fieldset, TabHolder, Container, Column, Col, Field
from xadmin.defs import ACTION_CHECKBOX_NAME

class BaseActionView(ModelAdminView):
    action_name = None  # key名，默认为类名
    verbose_name = None
    icon = 'fa fa-tasks'

    model_perm = None   #模型权限 'view', 'add', 'change', 'delete'
    perm = None #自定义权限
    log = False

    @classmethod
    def has_perm(cls, list_view):
        if cls.model_perm:
            perm_code = cls.model_perm
        else:
            perm_code = cls.perm or 'not_setting_perm'
            perm_code= 'auth.'+perm_code
        return list_view.has_permission(perm_code)

    def init_action(self, list_view):
        self.list_view = list_view
        self.admin_site = list_view.admin_site
        
    def get_redirect_url(self):
        action_return_url = self.request.META['HTTP_REFERER']
        return action_return_url

    def action(self, queryset):
        pass

    @filter_hook
    def do_action(self, queryset):
        return self.action(queryset)
    
Action = BaseActionView

class FormAction(Action):
    form = forms.Form
    form_layout = None
    form_template = 'xadmin/views/model_form_action.html'
    action_url = ''
    
    def get_form_datas(self):
        data = {'initial': self.get_initial_data()}
        if self.request_method == 'post' and '_save' in self.request.POST:
            data.update({'data': self.request.POST, 'files': self.request.FILES})
            
        else:
            data['initial'].update(self.request.GET)
        return data
    
    def get_initial_data(self):
        return {}
    
    @filter_hook
    def get_form_layout(self):
        layout = copy.deepcopy(self.form_layout)
        fields = self.form_obj.fields.keys()

        if layout is None:
            layout = Layout(Container(Col('full',
                Fieldset("", *fields, css_class="unsort no_title"), horizontal=True, span=12)
            ))
        elif type(layout) in (list, tuple) and len(layout) > 0:
            if isinstance(layout[0], Column):
                fs = layout
            elif isinstance(layout[0], (Fieldset, TabHolder)):
                fs = (Col('full', *layout, horizontal=True, span=12),)
            else:
                fs = (Col('full', Fieldset("", *layout, css_class="unsort no_title"), horizontal=True, span=12),)

            layout = Layout(Container(*fs))

            rendered_fields = [i[1] for i in layout.get_field_names()]
            container = layout[0].fields
            other_fieldset = Fieldset(_(u'Other Fields'), *[f for f in fields if f not in rendered_fields])

            if len(other_fieldset.fields):
                if len(container) and isinstance(container[0], Column):
                    container[0].fields.append(other_fieldset)
                else:
                    container.append(other_fieldset)

        return layout
    
    @filter_hook
    def get_form_helper(self):
        helper = FormHelper()
        helper.form_tag = False
        helper.add_layout(self.get_form_layout())

        return helper
    
    def setup_forms(self):
        helper = self.get_form_helper()
        if helper:
            self.form_obj.helper = helper
            
    @filter_hook
    def get_media(self):
        return super(FormAction, self).get_media() + self.form_obj.media + \
            self.vendor('xadmin.page.form.js', 'xadmin.form.css')
            
    @filter_hook
    def prepare_form(self):
        self.view_form = self.form
            
    @filter_hook
    def instance_forms(self):
        self.form_obj = self.view_form(**self.get_form_datas())
        
    def get_redirect_url(self):
        action_return_url = self.request.POST.get('_action_return_url')
        return action_return_url

    def action(self, queryset):
        pass

    def do_action(self, queryset):
        self.prepare_form()
        self.instance_forms()
        self.setup_forms()
        
        if self.request.POST.get('post') and '_save' in self.request.POST:
            if self.form_obj.is_valid():
                ret = self.action(queryset)
                if ret:
                    if isinstance(ret, basestring):
                        self.message_user(ret,'error')
                    elif isinstance(ret, HttpResponse):
                        return ret
                else:
                    self.message_user(u'操作成功', 'success')
                    return None
            
        context = self.get_context()
        context.update({
            'title': self.verbose_name or self.__class__.__bases__ [1].__name__,
            'form': self.form_obj,
            'queryset': queryset,
            'count': len(queryset),
            "opts": self.opts,
            "app_label": self.app_label,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
            'action_name': 'act_'+ self.__class__.__bases__ [1].__name__,
            'return_url': self.request.POST.get('_action_return_url') if '_action_return_url' in self.request.POST else self.request.META['HTTP_REFERER'],
            'action_url': self.action_url
        })
        
        return TemplateResponse(self.request, self.form_template, context, current_app=self.admin_site.name)