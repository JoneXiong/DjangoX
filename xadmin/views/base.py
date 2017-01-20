# coding=utf-8
import sys
import copy
import functools

from functools import update_wrapper


from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.template import Context, Template
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator, classonlymethod
from django.utils.http import urlencode
from django.utils.itercompat import is_iterable
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View

from ..util import static, json, vendor, sortkeypicker
from .. import defs
from structs import filter_hook
from ..dutils import JSONEncoder


csrf_protect_m = method_decorator(csrf_protect)


def inclusion_tag(file_name, context_class=Context, takes_context=False):
    """
    为 AdminView 的 block views 提供的便利方法，作用等同于 :meth:`django.template.Library.inclusion_tag`
    """
    def wrap(func):
        @functools.wraps(func)
        def method(self, context, nodes, *arg, **kwargs):
            _dict = func(self, context, nodes, *arg, **kwargs)
            from django.template.loader import get_template, select_template
            if isinstance(file_name, Template):
                t = file_name
            elif not isinstance(file_name, basestring) and is_iterable(file_name):
                t = select_template(file_name)
            else:
                t = get_template(file_name)
            new_context = context_class(_dict, **{
                'autoescape': context.autoescape,
                'current_app': context.current_app,
                'use_l10n': context.use_l10n,
                'use_tz': context.use_tz,
            })
            # 添加 admin_view
            new_context['admin_view'] = context['admin_view']
            csrf_token = context.get('csrf_token', None)
            if csrf_token is not None:
                new_context['csrf_token'] = csrf_token
            nodes.append(t.render(new_context))

        return method
    return wrap


class Common(object):

    def get_view(self, view_class, option_class=None, *args, **kwargs):
        """
        获取经过合并后的实际的view类
        获取 AdminViewClass 的实例。实际上就是调用 xadmin.sites.AdminSite.get_view_class 方法

        :param view_class: AdminViewClass 的类
        :param option_class: 希望与 AdminViewClass 合并的 OptionClass
        """
        opts = kwargs.pop('opts', {})
        return self.admin_site.get_view_class(view_class, option_class, **opts)(self.request, *args, **kwargs)

    def get_model_view(self, view_class, model, *args, **kwargs):
        """
        操作对象的获取
        获取 ModelAdminViewClass 的实例。首先通过 :xadmin.sites.AdminSite 取得 model 对应的 OptionClass，然后调用 get_view 方法

        :param view_class: ModelAdminViewClass 的类
        :param model: 绑定的 Model 类
        """
        return self.get_view(view_class, self.admin_site._registry.get(model), *args, **kwargs)

    def get_admin_url(self, name, *args, **kwargs):
        """
        路径工具函数
        通过 name 取得 url，会加上 AdminSite.app_name 的 url namespace
        """
        return reverse('%s:%s' % (self.admin_site.app_name, name), args=args, kwargs=kwargs)

    def get_model_url(self, model, name, *args, **kwargs):
        """
        name  为 add、changelist
        """
        return self.admin_site.get_model_url(model, name, *args, **kwargs)

    def get_model_perm(self, model, name):
        return '%s.%s_%s' % (model._meta.app_label, name, model._meta.module_name)

    def has_model_perm(self, model, name, user=None):
        """
        name  为 view、change
        """
        user = user or self.user
        return user.has_perm(self.get_model_perm(model, name)) or (name == 'view' and self.has_model_perm(model, 'change', user))

    ########################################## HTTP 相关的函数 ##########################################
    def get_query_string(self, new_params=None, remove=None):
        """
        URL 参数控制
        在当前的query_string基础上生成新的query_string

        :param new_params: 要新加的参数，该参数为 dict 
        :param remove: 要删除的参数，该参数为 list, tuple
        """
        if new_params is None:
            new_params = {}
        if remove is None:
            remove = []
        p = dict(self.request.GET.items()).copy()
        for r in remove:
            for k in p.keys():
                if k.startswith(r):
                    del p[k]
        for k, v in new_params.items():
            if v is None:
                if k in p:
                    del p[k]
            else:
                p[k] = v
        return '?%s' % urlencode(p)

    def get_form_params(self, new_params=None, remove=None):
        """
        Form 参数控制
        将当前 request 的参数，新加或是删除后，生成 hidden input。用于放入 HTML 的 Form 中。

        :param new_params: 要新加的参数，该参数为 dict 
        :param remove: 要删除的参数，该参数为 list, tuple
        """
        if new_params is None:
            new_params = {}
        if remove is None:
            remove = []
        p = dict(self.request.GET.items()).copy()
        for r in remove:
            for k in p.keys():
                if k.startswith(r) and k!='pop':
                    del p[k]
        for k, v in new_params.items():
            if v is None:
                if k in p:
                    del p[k]
            else:
                p[k] = v
        return mark_safe(''.join(
            '<input type="hidden" name="%s" value="%s"/>' % (k, v) for k, v in p.items() if v))
        
        
    def get_param(self, k):
        ret = self.request.GET.get(k, None)
        if ret:
            return ret
        else:
            return self.request.POST.get(k, None)
        
    def param_list(self):
        return self.request.GET.keys() + self.request.POST.keys()

    ########################################## 页面Page 相关的函数 ##########################################
    def render_response(self, content, response_type='json'):
        """
        请求返回API
        便捷方法，方便生成 HttpResponse，如果 response_type 为 ``json`` 会自动转为 json 格式后输出
        """
        if response_type == 'json':
            response = HttpResponse(content_type='application/json; charset=UTF-8')
            response.write(
                json.dumps(content, cls=JSONEncoder, ensure_ascii=False))
            return response
        return HttpResponse(content)
    
    def render_json(self, content):
        response = HttpResponse(content_type='application/json; charset=UTF-8')
        response.write(
            json.dumps(content, cls=JSONEncoder, ensure_ascii=False))
        return response
    
    def render_text(self, content):
        return HttpResponse(content)

    def template_response(self, template, context):
        return self.render_tpl(template, context)
    
    def render_tpl(self, tpl, context):
        return TemplateResponse(self.request, tpl, context, current_app=self.admin_site.name)

    def message_user(self, message, level='info'):
        """
        debug error info success warning
        posts a message using the django.contrib.messages backend.
        """
        if hasattr(messages, level) and callable(getattr(messages, level)):
            getattr(messages, level)(self.request, message)
    
    def msg(self, message, level='info'):
        '''
        level 为 info、success、error
        '''
        self.message_user(message, level)

    def static(self, path):
        """
        路径工具函数
        :meth:`xadmin.util.static` 的快捷方法，返回静态文件的 url。
        """
        return static(path)

    def vendor(self, *tags):
        return vendor(*tags)
    
    
    ########################################## 日志操作相关的函数 ##########################################
    def log_change(self, obj, message):
        """
        写对象日志
        """
        from django.contrib.admin.models import CHANGE
        from django.contrib.contenttypes.models import ContentType
        from django.utils.encoding import force_text
        type_id = ContentType.objects.get_for_model(obj).pk
        obj_id = obj.pk
        obj_des = force_text(obj)
        aciton_id = CHANGE
        self._log(type_id, obj_id, obj_des, aciton_id, message)
        
    def _log(self, type_id, obj_id, obj_des, aciton_id, msg=''):
        from django.contrib.admin.models import LogEntry
        LogEntry.objects.log_action(
            user_id         = self.request.user.pk,
            content_type_id = type_id,
            object_id       = obj_id,
            object_repr     = obj_des,
            action_flag     = aciton_id,
            change_message  = msg
        )


class BasePlugin(Common):
    """
    所有 Plugin 的基类。继承于 :class:`Common` 。插件的注册和使用可以参看 :meth:`xadmin.sites.AdminSite.register_plugin` ，
    插件的原理可以参看 :func:`filter_hook` :

    .. autofunction:: xadmin.views.base.filter_hook
    """
    def __init__(self, admin_view):
        self.admin_view = admin_view
        self.admin_site = admin_view.admin_site

        if hasattr(admin_view, 'model'):
            self.model = admin_view.model
            self.opts = admin_view.model._meta
        else:
            self.model = None
            self.opts = None

    def init_request(self, *args, **kwargs):
        """
        插件的初始化方法，Plugin 实例化后被调用的第一个方法。该方法主要用于初始化插件需要的属性，
        同时判断当前请求是否需要加载该插件，例如 Ajax插件的实现方式::

            def init_request(self, *args, **kwargs):
                return bool(self.request.is_ajax() or '_ajax' in self.param_list() )

        当返回值为 ``False`` 时，所属的 AdminView 实例不会加载该插件
        """
        pass


class BaseView(Common, View):
    """
    所有 View 的基类。继承于 :Common 和 django.views.generic.View

    xadmin 每次请求会产生一个 ViewClass 的实例，也就是基于 Class 的 view 方式。该方式在 Django 1.3 被实现，可以参看 Django 的官方文档

    使用 Class 的方式实现的好处显而易见: 每一次请求都会产生一个新的实例，request 这种变量就可以保存在实例中，复写父类方法时再也不用带着 request 到处跑了，
    当然，除了 request 还有很多可以基于实例存储的变量。

    其次，基于实例的方式非常方便的实现了插件功能，而且还能实现插件的动态加载，因为每个 View 实例可以根据自身实例的属性情况来判断加载哪些插件
    """

    base_template = 'xadmin/base.html'
    need_site_permission = True
    csrf = True

    def __init__(self, request, *args, **kwargs):
        self.request = request
        self.request_method = request.method.lower()
        self.user = request.user

        self.base_plugins = [p(self) for p in getattr(self,
                                                      "plugin_classes", [])]    #Plugin真正实例化的地方

        self.args = args
        self.kwargs = kwargs
        self.init_plugin(*args, **kwargs)   #实例化时执行
        self.init_request(*args, **kwargs)  #实例化时执行

    @classonlymethod
    def as_view(cls):
        """
        复写了 django View 的as_view 方法，主要是将 :meth:`View.dispatch` 的也写到了本方法中，并且去掉了一些初始化操作，
        因为这些初始化操作在 AdminView 的初始化方法中已经完成了，可以参看 :meth:`BaseView.init_request`
        """
        def view(request, *args, **kwargs):
            self = cls(request, *args, **kwargs)    #真正实例化的地方

            if hasattr(self, 'get') and not hasattr(self, 'head'):
                self.head = self.get

            if self.request_method in self.http_method_names:
                handler = getattr(
                    self, self.request_method, self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed

            return handler(request, *args, **kwargs)

        update_wrapper(view, cls, updated=())
        view.need_site_permission = cls.need_site_permission
        view.login_view = getattr(cls, 'login_view', None)
        if not cls.csrf:
            view.csrf_exempt = True
        return view

    def init_request(self, *args, **kwargs):
        """
        一般用于子类复写的初始化方法，在 AdminView 实例化时调用，:class:`BaseView` 的该方法不做任何操作。
        """
        pass

    def init_plugin(self, *args, **kwargs):
        """
        AdminView 实例中插件的初始化方法，在 :meth:`BaseView.init_request` 后调用。根据 AdminView 中
        的 base_plugins 属性将插件逐一初始化，既调用 :meth:`BasePlugin.init_request` 方法，并根据返回结果判断是否加载该插件。
        最后该方法会将初始化后的插件设置为 plugins 属性。
        """
        plugins = []
        for p in self.base_plugins:
            p.request = self.request
            p.user = self.user
            p.args = self.args
            p.kwargs = self.kwargs
            result = p.init_request(*args, **kwargs)
            if result is not False:
                # 返回结果不为 `False` 就加载该插件
                plugins.append(p)
        self.plugins = plugins

    @filter_hook
    def get_context(self):
        """
        返回显示页面所需的 context 对象。
        """
        return {'admin_view': self, 'media': self.media, 'base_template': self.base_template}

    @property
    def media(self):
        return self.get_media()

    @filter_hook
    def get_media(self):
        """
        取得页面所需的 Media 对象，用于生成 css 和 js 文件
        """
        return forms.Media()


class SiteView(BaseView):

    base_template = 'xadmin/base_site.html'    #: View模板继承的基础模板

    def _check_menu_permission(self, item):
        need_perm = item.pop('perm', None)
        if need_perm is None:
            return True
        elif callable(need_perm):
            return need_perm(self.user)
        elif need_perm == 'super':    # perm项如果为 super 说明需要超级用户权限
            return self.user.is_superuser
        else:
            return self.user.has_perm(need_perm)
        
    def get_nav_menu(self, app_label=None):
        # 非DEBUG模式会首先尝试从SESSION中取得缓存的 app 菜单项
        menu_session_key = app_label and 'nav_menu_%s'%app_label or 'nav_menu'
        if not settings.DEBUG and menu_session_key in self.request.session:
            nav_menu = json.loads(self.request.session[menu_session_key])
        else:
            if app_label:
                menus = copy.deepcopy(self.admin_site.get_app_menu(app_label)) #copy.copy(self.get_nav_menu())
            else:
                menus = copy.deepcopy(self.admin_site.get_menu())

            def filter_item(item):
                if 'menus' in item:
                    #before_filter_length = len(item['menus'])
                    item['menus'] = [filter_item(
                        i) for i in item['menus'] if self._check_menu_permission(i)]
                    after_filter_length = len(item['menus'])
                    if after_filter_length == 0:
                        return None
                return item

            nav_menu = [filter_item(item) for item in menus if self._check_menu_permission(item)]
            nav_menu = filter(lambda x:x, nav_menu)

            if not settings.DEBUG:
                self.request.session[menu_session_key] = json.dumps(nav_menu)
                self.request.session.modified = True
        return nav_menu

    def get_site_menu(self):
        if hasattr(self, 'app_label'):
            menus = self.admin_site.get_site_menu(self.app_label)
            return menus
        else:
            return []
 
    def deal_selected(self, nav_menu):
        def check_selected(menu, path):
            # 判断菜单项是否被选择，使用当前url跟菜单项url对比
            selected = False
            if 'url' in menu:
                chop_index = menu['url'].find('?')
                if chop_index == -1:
                    selected = path.startswith(menu['url'])
                else:
                    selected = path.startswith(menu['url'][:chop_index])
            if 'menus' in menu:
                for m in menu['menus']:
                    _s = check_selected(m, path)
                    if _s:
                        selected = True
            if selected:
                menu['selected'] = True
            return selected
        for menu in nav_menu:
            if check_selected(menu, self.request.path):break

    @filter_hook
    def get_context(self):
        """
        **Context Params** :
            ``nav_menu`` : 权限过滤后的系统菜单项，如果在非 DEBUG 模式，该项会缓存在 SESSION 中
        """
        context = super(SiteView, self).get_context()

        nav_menu = []
        if '_pop' not in self.request.GET:
            _app_label = hasattr(self, 'app_label') and self.app_label or None
            nav_menu = self.get_nav_menu(_app_label)
            self.deal_selected(nav_menu)
        
        m_site = self.admin_site
        context.update({
            'menu_template': defs.BUILDIN_STYLES.get(m_site.menu_style, defs.BUILDIN_STYLES['default']), 
            'nav_menu': nav_menu,
            'site_menu': self.get_site_menu(),
            'site_title': m_site.site_title or defs.DEFAULT_SITE_TITLE,
            'site_footer': m_site.site_footer or defs.DEFAULT_SITE_FOOTER,
            'breadcrumbs': self.get_breadcrumb(),
            'head_fix': m_site.head_fix
        })

        return context

    @filter_hook
    def get_model_icon(self, model):
        icon = None
        if model in self.admin_site._registry:
            # 如果 Model 的 OptionClass 中有 model_icon 属性，则使用该属性
            icon = getattr(self.admin_site._registry[model],
                           'model_icon', defs.DEFAULT_MODEL_ICON)
        return icon
    
    def block_top_account_menu(self, context, nodes):
        a_class = self.admin_site.head_fix and 'class="J_menuItem"' or '' 
        return '<li><a %s href="%s"><i class="fa fa-key"></i> %s</a></li>' % (a_class, self.get_admin_url('account_password'), _('Change Password'))

    @filter_hook
    def get_breadcrumb(self):
        u'''
        导航链接基础部分
        '''
        import xadmin
        if self.admin_site.head_fix:
            return []
        base = [{
            'url': self.get_admin_url('index'),
            'title': _('Home')
            }]
        if hasattr(self, 'app_label') and self.app_label:
            app_mod = self.admin_site.app_dict[self.app_label]
            pref_url = xadmin.ROOT_PATH_NAME and '/'+xadmin.ROOT_PATH_NAME or ''
            base.append({
                         'url': app_mod.index_url,#'%s/index/%s/'%(pref_url, self.app_label),
                         'title':  hasattr(app_mod,'verbose_name') and app_mod.verbose_name or self.app_label
                         })
        return base


BaseAdminPlugin = BasePlugin
BaseAdminView = BaseView
CommAdminView = SiteView
