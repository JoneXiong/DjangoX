# -*- coding: utf-8 -*-
'''
一些站点级视图
'''
from django.utils.translation import ugettext_lazy,ugettext as _
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.views.decorators.cache import never_cache
from django.contrib.auth.views import login
from django.contrib.auth.views import logout
from django.http import HttpResponse,HttpResponseRedirect
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate

from base import BaseView, filter_hook, SiteView
from dashboard import Dashboard
from xadmin.models import UserSettings
from xadmin.layout import FormHelper
from xadmin import defs


class IndexView(Dashboard):
    title = _("Main Dashboard")
    icon = "fa fa-dashboard"

    def get_page_id(self):
        return 'home'

class MainView(SiteView):
    title = _("Main Dashboard")
    template = 'xadmin/main.html'
    app_label = None

    @filter_hook
    def get_context(self):
        context = {
                'admin_view': self, 
                'media': self.media, 
                'base_template': self.base_template
                }
        
        nav_menu = self.get_nav_menu()
        m_site = self.admin_site
        context.update({
            'menu_template': defs.BUILDIN_STYLES['inspinia'], 
            'nav_menu': nav_menu,
            #'site_menu': hasattr(self, 'app_label') and m_site.get_site_menu(self.app_label) or [],
            'site_title': m_site.site_title or defs.DEFAULT_SITE_TITLE,
            'site_footer': m_site.site_footer or defs.DEFAULT_SITE_FOOTER,
            #'breadcrumbs': self.get_breadcrumb(),
            #'head_fix': m_site.head_fix
        })
        return context

    @never_cache
    def get(self, request, *args, **kwargs):
        return self.template_response(self.template, self.get_context())


class UserSettingView(BaseView):

    @never_cache
    def post(self, request):
        key = request.POST['key']
        val = request.POST['value']
        us, created = UserSettings.objects.get_or_create(
            user=self.user, key=key)
        us.value = val
        us.save()
        return HttpResponse('')

class AdminAuthenticationForm(AuthenticationForm):
    """
    A custom authentication form used in the admin app.

    """
    this_is_the_login_form = forms.BooleanField(
        widget=forms.HiddenInput, initial=1,
        error_messages={'required': ugettext_lazy("Please log in again, because your session has expired.")})

    def clean(self):
        from xadmin.util import User
        
        ERROR_MESSAGE = ugettext_lazy("Please enter the correct username and password "
                                      "for a staff account. Note that both fields are case-sensitive.")
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        message = ERROR_MESSAGE

        if username and password:
            self.user_cache = authenticate(
                username=username, password=password)
            if self.user_cache is None:
                if u'@' in username:
                    # Mistakenly entered e-mail address instead of username? Look it up.
                    try:
                        user = User.objects.get(email=username)
                    except (User.DoesNotExist, User.MultipleObjectsReturned):
                        # Nothing to do here, moving along.
                        pass
                    else:
                        if user.check_password(password):
                            message = _("Your e-mail address is not your username."
                                        " Try '%s' instead.") % user.username
                raise forms.ValidationError(message)
            elif not self.user_cache.is_active or not self.user_cache.is_staff:
                raise forms.ValidationError(message)
        if hasattr(self, 'check_for_test_cookie'):
            self.check_for_test_cookie()
        return self.cleaned_data

class LoginView(BaseView):

    title = _(u"登陆")
    login_form = None
    login_template = None

    @filter_hook
    def update_params(self, defaults):
        pass

    @never_cache
    def get(self, request, *args, **kwargs):
        context = self.get_context()
        helper = FormHelper()
        helper.form_tag = False
        context.update({
            'title': self.title,
            'helper': helper,
            'app_path': request.get_full_path(),
            REDIRECT_FIELD_NAME: request.get_full_path(),
        })
        defaults = {
            'extra_context': context,
            'current_app': self.admin_site.name,
            'authentication_form': self.login_form or AdminAuthenticationForm,
            'template_name': self.login_template or 'xadmin/auth/login.html',
        }
        self.update_params(defaults)
        return login(request, **defaults)

    @never_cache
    def post(self, request, *args, **kwargs):
        return self.get(request)


class LogoutView(BaseView):

    logout_template = None
    need_site_permission = False

    @filter_hook
    def update_params(self, defaults):
        pass

    @never_cache
    def get(self, request, *args, **kwargs):
        context = self.get_context()
        defaults = {
            'extra_context': context,
            'current_app': self.admin_site.name,
            'template_name': self.logout_template or 'xadmin/views/logged_out.html',
        }
        if self.logout_template is not None:
            defaults['template_name'] = self.logout_template

        self.update_params(defaults)
        logout(request, **defaults)
        return HttpResponseRedirect(self.get_admin_url('index'))

    @never_cache
    def post(self, request, *args, **kwargs):
        return self.get(request)
