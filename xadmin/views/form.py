# coding=utf-8

import copy

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.forms.models import modelform_factory
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.encoding import force_unicode
from django.utils.html import escape
from django.template import loader
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.http import HttpResponse

from xadmin import widgets
from xadmin.layout import FormHelper, Layout, Fieldset, TabHolder, Container, Column, Col, Field
from xadmin.util import unquote
from xadmin.views.detail import DetailAdminUtil
from .common import JsonErrorDict
from xadmin import dutils

from base import SiteView, filter_hook, csrf_protect_m

class FormView(SiteView):
    form = forms.Form
    verbose_name = None
    readonly_fields = ()

    template = 'xadmin/views/form.html'

    form_layout = None
    pop = False
    #弃用
    title = None
    
    _has_file_field = False
    perm = None

    def init_request(self, *args, **kwargs):
        # comm method for both get and post
        perm_code = self.perm or 'not_setting_perm'
        if not self.user.has_perm('auth.'+perm_code):
            raise PermissionDenied
        self.prepare_form()
        if '_pop' in self.request.GET:
            self.pop = True
            self.base_template = 'xadmin/base_pure.html'

    @filter_hook
    def prepare_form(self):
        self.view_form = self.form

    @filter_hook
    def instance_forms(self):
        self.form_obj = self.view_form(**self.get_form_datas())

    def setup_forms(self):
        helper = self.get_form_helper()
        if helper:
            self.form_obj.helper = helper
        self.check_fields()
            
    def check_fields(self):
        for name, field in self.form_obj.fields.items():
            if isinstance(field,forms.FileField):
                self._has_file_field = True

    @filter_hook
    def valid_forms(self):
        return self.form_obj.is_valid()

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

    @filter_hook
    def save_forms(self):
        pass

    @csrf_protect_m
    @filter_hook
    def get(self, request, *args, **kwargs):
        self.instance_forms()
        self.setup_forms()

        return self.get_response()

    @csrf_protect_m
    @dutils.commit_on_success
    @filter_hook
    def post(self, request, *args, **kwargs):
        self.instance_forms()
        self.setup_forms()

        if self.valid_forms():
            ret = self.save_forms()
            if isinstance(ret, basestring):
                self.message_user(ret,'error')
                return self.get_response()
            if isinstance(ret, HttpResponse):
                return ret
            response = self.post_response()
            if isinstance(response, basestring):
                return HttpResponseRedirect(response)
            else:
                return response
        else:
            if self.request.is_ajax() or self.request.GET.get('_ajax'):
                result = {}
                result['result'] = 'error'
                result['errors'] = JsonErrorDict(self.form_obj.errors, self.form_obj).as_json()
                return self.render_response(result)

        return self.get_response()
    
    @filter_hook
    def get_error_list(self):
        """
        获取表单的错误信息列表。
        """
        return JsonErrorDict(self.form_obj.errors, self.form_obj).as_json()

    @filter_hook
    def get_context(self):
        context = super(FormView, self).get_context()
        context.update({
            'form': self.form_obj,
            'title': self.verbose_name or self.title,
            'nav_buttons': mark_safe(' '.join(self.get_nav_btns()) ),
            'errors': self.get_error_list(),
            'has_file_field': self._has_file_field,
        })
        return context
    
    def get_nav_btns(self):
        return []

    @filter_hook
    def get_media(self):
        return super(FormView, self).get_media() + self.form_obj.media + \
            self.vendor('xadmin.page.form.js', 'xadmin.form.css')

    def get_initial_data(self):
        return {}

    @filter_hook
    def get_form_datas(self):
        data = {'initial': self.get_initial_data()}
        if self.request_method == 'get':
            data['initial'].update(self.request.GET)
        else:
            data.update({'data': self.request.POST, 'files': self.request.FILES})
        return data

    @filter_hook
    def get_response(self):
        context = self.get_context()
        context.update(self.kwargs or {})

        return TemplateResponse(
            self.request, self.template,
            context, current_app=self.admin_site.name)

    @filter_hook
    def post_response(self):

        msg = _('操作成功')
        self.message_user(msg, 'success')
        param_list = self.param_list()
        
        if "_continue" in param_list:
            if self._has_file_field:
                return self.request.get_full_path()
            return self.get_response()
        elif "_redirect" in param_list:
            return self.get_param('_redirect')
        elif '_pop' in param_list:
            js_str='''<!DOCTYPE html>
<html lang="zh_CN">
<head>
            <script type="text/javascript">
                window.opener.location.reload();
                window.close();
            </script>
</head><body></body>
</html>
            '''
            return HttpResponse(mark_safe(js_str))
        else:
            return self.get_redirect_url()

    @filter_hook
    def get_redirect_url(self):
        return self.get_admin_url('index')

FormAdminView = FormView
