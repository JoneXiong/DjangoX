# coding=utf-8
import sys
from functools import update_wrapper

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models.base import ModelBase
from django.views.decorators.cache import never_cache
from django.utils.text import capfirst
from django.core.urlresolvers import reverse

from util import sortkeypicker
from core.structs import SortedDict
import defs

#设置系统的编码为utf-8
reload(sys)
sys.setdefaultencoding("utf-8")


class AlreadyRegistered(Exception):
    """
    如果一个 model 已经在 AdminSite 注册过，当尝试再次注册时会抛出这个异常。
    """
    pass


class NotRegistered(Exception):
    """
    当一个model并未在 AdminSite 注册，当调用 AdminSite.unregister 想要取消该model的注册就会抛出该异常。
    """
    pass


class MergeAdminMetaclass(type):
    """
    用来生成 admin view class 的原类。

    目前该原类没有做什么特殊的工作。接下来的版本该原类可能会给 admin view class 注入一些公共的属性。
    """
    def __new__(cls, name, bases, attrs):
        return type.__new__(cls, str(name), bases, attrs)


class AdminSite(object):
    """
    全局管理对象
    xadmin最核心的类，管理整个xadmin站点的所有注册内容。

        * 创建 ``admin view class``
        * 注册 django urls

    其中，xadmin 需要的信息包括以下信息：

        * 需要 xadmin 管理的 models，以及各 model 的 admin 信息
        * 注册的 ``admin view class``
        * 注册的 ``model admin view class``
        * 注册的各种插件
    """
    
    site_title = None         # 网站的标题
    site_footer = None         # 网站的下角标文字
    menu_style = 'accordion'    # 网站左侧菜单风格 可选项 default、accordion
    head_fix = False
    app_dict = SortedDict()   # app模块全局字典
    sys_menu = {}                   # 网站菜单全局字典
    sys_menu_loaded = False  # 菜单是否加载过
    apps_icons = {'xadmin': 'fa fa-circle-o'}

    login_view = None
    main_view = None #frame框架main页试图
    show_default_index = True

    
    def __init__(self, name='xadmin'):
        self.name = name
        self.app_name = 'xadmin'

        self._registry = {}  # model_class class -> admin_class class    模型类全局字典
        self._registry_avs = {}  # admin_view_class class -> admin_class class    型管理类全局字典
        self._registry_settings = {}  # settings name -> admin_class class
        self._registry_views = []   #他非模型视图集合
        self._registry_pages = []   #Page模型集合

        #: 保存所有 Model Base Admin View Class    型视图集合
        self._registry_modelviews = []

        #: 保存所有系统插件信息， 
        #    *key*   : 插件绑定的 AdminView 类 
        #    *value* : 插件类
        self._registry_plugins = {}

        #: 创建好的 AdminView 会被缓存起来，同样的， 
        #    *key*   : 需要创建的 AdminView 的 class name
        #    *value* : 已经缓存的 AdminView 类
        self._admin_view_cache = {}

        self.check_dependencies()

        self.model_admins_order = 0 # 当前系统分配菜单的索引值

    def copy_registry(self):
        """
        复制当前 AdminSite 实例的信息
        """
        import copy
        return {
            'models': copy.copy(self._registry),
            'avs': copy.copy(self._registry_avs),
            'views': copy.copy(self._registry_views),
            'settings': copy.copy(self._registry_settings),
            'modelviews': copy.copy(self._registry_modelviews),
            'plugins': copy.copy(self._registry_plugins),
        }

    def restore_registry(self, data):
        """
        恢复当前 AdminSite 实例的信息
        """
        self._registry = data['models']
        self._registry_avs = data['avs']
        self._registry_views = data['views']
        self._registry_settings = data['settings']
        self._registry_modelviews = data['modelviews']
        self._registry_plugins = data['plugins']

    def register_modelview(self, path, admin_view_class, name):
        """
        注册 ModelAdminView 子类

        :param path: url路径
        :param admin_view_class: 注册的 ModelAdminView 子类
        :param name:  view对应的url name, 要包含两个%%s, 分别会替换为 app_label和module_name

        注册 Model Base Admin View 可以为每一个在xadmin注册的 Model 生成一个 Admin View，并且包含相关的 Model 信息。
        """
        # 内部引用，避免循环引用
        from xadmin.views.base import BaseView
        if issubclass(admin_view_class, BaseView):
            self._registry_modelviews.append((path, admin_view_class, name))
        else:
            raise ImproperlyConfigured(u'The registered view class %s isn\'t subclass of %s' %(admin_view_class.__name__, BaseView.__name__))

    def register_view(self, path, admin_view_class, name, update=False):
        """
        注册 AdminView 类，一般用于创建独立的 admin 页面，例如登陆，介绍页面，帮助页面等。

        :param path:  url路径
        :param admin_view_class: 注册的 AdminView 类
        :param name: view对应的url name
        """
        if update==False:
            self._registry_views.append((path, admin_view_class, name))
        else:
            self._registry_views.insert(0,(path, admin_view_class, name))

    def register_page(self, page_view_class):
        name = page_view_class.__name__
        self._registry_pages.append(page_view_class)
        self.register_view('^page/%s/$'%name.lower(), page_view_class, name)
        
    def register_appindex(self, app_index_class):
        app_label = app_index_class.app_label
        name = '%s_%s'%(app_label,app_index_class.__name__)
        self.app_dict[app_label].index_url_name = name
        self.register_view('^index/%s/$'%app_label, app_index_class, name)

    def register_plugin(self, plugin_class, admin_view_class):
        """
        注册 Plugin 类，当任何 AdminView 运行时当前 view 绑定的 plugin 会生效。

        :param plugin_class: 插件类
        :param admin_view_class: 该 plugin 绑定的 AdminView 类
        """
        from xadmin.views.base import BasePlugin
        if issubclass(plugin_class, BasePlugin):
            self._registry_plugins.setdefault(
                admin_view_class, []).append(plugin_class)
        else:
            raise ImproperlyConfigured(u'The registered plugin class %s isn\'t subclass of %s' %(plugin_class.__name__, BasePlugin.__name__))

#    def register_settings(self, name, admin_class):
#        self._registry_settings[name.lower()] = admin_class

    def register(self, model_or_iterable, admin_class=object, **options):
        """
        注册需要管理的 Model， 或是为某 AdminView 添加 OptionClass

        :param model_or_iterable: 传入 model 或 BaseView子类
        :param admin_class: 
                        model_or_iterable 为 Model 时，该参数为 ModelAdmin；
                        model_or_iterable 为 BaseView 时 ，该参数为 OptionClass
        """
        from xadmin.views.base import BaseView
        if isinstance(model_or_iterable, ModelBase) or issubclass(model_or_iterable, BaseView):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if isinstance(model, ModelBase):    #当为模型Model时
                if model._meta.abstract:
                    raise ImproperlyConfigured('The model %s is abstract, so it cannot be registered with admin.' % model.__name__)

                if model in self._registry:
                    raise AlreadyRegistered('The model %s is already registered' % model.__name__)

                # If we got **options then dynamically construct a subclass of
                # admin_class with those **options.
                if options:
                    # For reasons I don't quite understand, without a __module__  the created class appears to "live" in the wrong place, which causes issues later on.
                    options['__module__'] = __name__

                admin_class = type(str("%s__%s__Admin" % (model._meta.app_label, model._meta.module_name)), (admin_class,), options or {})
                admin_class.model = model
                if not hasattr(admin_class, "order"):
                    admin_class.order = self.model_admins_order
                    self.model_admins_order += 1
                self._registry[model] = admin_class
            else:   # 当为BaseView子类时
                if model in self._registry_avs:
                    raise AlreadyRegistered('The admin_view_class %s is already registered' % model.__name__)
                if options:
                    options['__module__'] = __name__
                    admin_class = type(str("%sAdmin" % model.__name__), (admin_class,), options)

                self._registry_avs[model] = admin_class

    def get_grup_registrys(self, grup_name):
        return [ (e.model, e) for e in self._registry.values() if e.model._meta.app_label==grup_name]

    def unregister(self, model_or_iterable):
        """
        取消 Model 或 OptionClass 的注册

        如果 Model 或 OptionClass 并未注册过，会抛出 :exc:`xadmin.sites.NotRegistered` 异常
        """
        from xadmin.views.base import BaseView
        if isinstance(model_or_iterable, (ModelBase, BaseView)):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if isinstance(model, ModelBase):
                if model not in self._registry:
                    raise NotRegistered(
                        'The model %s is not registered' % model.__name__)
                del self._registry[model]
            else:
                if model not in self._registry_avs:
                    raise NotRegistered('The admin_view_class %s is not registered' % model.__name__)
                del self._registry_avs[model]

    def set_loginview(self, login_view):
        self.login_view = login_view

    def has_permission(self, request):
        """
        如果返回为 ``True`` 则说明 ``request.user`` 至少能够访问当前xadmin网站。否则无法访问xadmin的任何页面。
        """
        return request.user.is_active and request.user.is_staff

    def check_dependencies(self):
        """
        检查运行xadmin需要的包是否已经正确安装

        默认情况下会检查 *ContentType* 模块是否已经正确安装
        """
        from django.contrib.contenttypes.models import ContentType

        if not ContentType._meta.installed:
            raise ImproperlyConfigured("Put 'django.contrib.contenttypes' in "
                                       "your INSTALLED_APPS setting in order to use the admin application.")
        if not ('django.contrib.auth.context_processors.auth' in settings.TEMPLATE_CONTEXT_PROCESSORS or
                'django.core.context_processors.auth' in settings.TEMPLATE_CONTEXT_PROCESSORS):
            raise ImproperlyConfigured("Put 'django.contrib.auth.context_processors.auth' "
                                       "in your TEMPLATE_CONTEXT_PROCESSORS setting in order to use the admin application.")

    def site_view_decor(self, view, cacheable=False):
        """
        为所有 View 提供公共装饰，访问权限验证
        在Site.get_urls 方法中使用该方法

        :param cacheable: 默认情况下，所有的 AdminView 会通过 ``never_cache`` 标记成不做缓存，如果确实需要缓存，可以设置 cacheable=True
        """
        def inner(request, *args, **kwargs):
            if not self.has_permission(request) and getattr(view, 'need_site_permission', True):
                # 没有权限则跳转到登录页
                _login_view = getattr(view, 'login_view', self.login_view) or self.login_view
                return self.create_admin_view(_login_view)(request, *args, **kwargs)
            return view(request, *args, **kwargs)

        if not cacheable:
            inner = never_cache(inner)
        return update_wrapper(inner, view)

    def _get_merge_attrs(self, option_class, plugin_class):
        """
        从 OptionClass 中获取 plugin 需要的属性。目前是获取 OptionClass 中不以 ``_`` 开头的属性，且该属性在 Plugin 中有定义

        TODO: 处理方式需要考虑优化，目前还是比较山寨
        """
        return dict([(name, getattr(option_class, name)) for name in dir(option_class)
                    if name[0] != '_' and not callable(getattr(option_class, name)) and hasattr(plugin_class, name)])

#    def _get_settings_class(self, admin_view_class):
#        name = admin_view_class.__name__.lower()
#
#        if name in self._registry_settings:
#            return self._registry_settings[name]
#        elif name.endswith('admin') and name[0:-5] in self._registry_settings:
#            return self._registry_settings[name[0:-5]]
#        elif name.endswith('adminview') and name[0:-9] in self._registry_settings:
#            return self._registry_settings[name[0:-9]]
#
#        return None

    def _create_plugin(self, option_classes):
        """
        创建插件类，用于创建新的、与 OptionClass 合并过的插件类。
        """
        # 创建新插件类的方法
        def merge_class(plugin_class):
            if option_classes:
                attrs = {}
                bases = [plugin_class]
                for oc in option_classes:
                    # 首先根据 OptionClass 获取需要合并的属性 
                    attrs.update(self._get_merge_attrs(oc, plugin_class))
                    # 其次查看 OptionClass 是否含有与插件类同名的 SubClass，有的话也作为 baseclass 合并。
                    meta_class = getattr(oc, plugin_class.__name__, getattr(oc, plugin_class.__name__.replace('Plugin', ''), None))
                    if meta_class:
                        bases.insert(0, meta_class)
                if attrs:
                    # 合并新的插件类
                    plugin_class = MergeAdminMetaclass(
                        '%s%s' % ('__'.join([oc.__name__ for oc in option_classes]), plugin_class.__name__),
                        tuple(bases), attrs)
            return plugin_class
        return merge_class

    def get_plugins(self, admin_view_class, *option_classes):
        """
        核心方法，用于获取 AdminViewClass 的 plugins。

        获取 plugins 首先根据该 AdminViewClass 及其所有的继承类在已经注册的插件中找到相应的插件类。然后再使用第二个参数的 OptionClass 拼成插件类。
        """
        from xadmin.views import BaseView
        from xadmin.views.page import GridPage
        plugins = []
        opts = [oc for oc in option_classes if oc]
        for klass in admin_view_class.mro():
            # 列出 AdminViewClass 所有的继承类，包括本身类
            if klass == BaseView or issubclass(klass, BaseView):
                merge_opts = []
                
                reg_class = self._registry_avs.get(klass)
                if reg_class:
                    merge_opts.append(reg_class)
                    
#                settings_class = self._get_settings_class(klass)
#                if settings_class:
#                    merge_opts.append(settings_class)
                if issubclass(klass, GridPage):
                    merge_opts.append(admin_view_class)
                    
                merge_opts.extend(opts)
                ps = self._registry_plugins.get(klass, [])
                # 如果有需要merge的 OptionClass 则使用 AdminSite._create_plugin 方法创建插件类，并且放入插件列表
                plugins.extend(map(self._create_plugin(
                    merge_opts), ps) if merge_opts else ps)
        return plugins

    def get_view_class(self, view_class, option_class=None, **opts):
        """
        最核心的方法，用于创建 AdminViewClass。

        创建 AdminView 和核心思想为动态生成 mix 的类，主要步骤有两步:

            1. 使用已经注册的 OptionClass (见 :meth:`~register`) 以及参数传入的 option_class 与 view_class 动态生成类
            2. 根据 view_class 及其继承类找到相应的 plugins， 作为生成的 AdminViewClass 的 plugins 属性

        """
        merges = [option_class] if option_class else []
        for klass in view_class.mro():
            # 找到该 view_class 所有基类在 AdminSite 注册的 OptionClass
            reg_class = self._registry_avs.get(klass)
            if reg_class:
                merges.append(reg_class)
#            settings_class = self._get_settings_class(klass)
#            if settings_class:
#                merges.append(settings_class)
            merges.append(klass)
            
        new_class_name = '__'.join([c.__name__ for c in merges])

        if new_class_name not in self._admin_view_cache:
            # 如果缓存中没有该类，则创建这个类。首先取得该 view_class 的 plugins
            plugins = self.get_plugins(view_class, option_class)
            # 合成新类，同时把 plugins 及 admin_site 作为类属性传入
            self._admin_view_cache[new_class_name] = MergeAdminMetaclass(new_class_name, tuple(merges),  dict({'plugin_classes': plugins, 'admin_site': self}, **opts))

        return self._admin_view_cache[new_class_name]

    def create_admin_view(self, admin_view_class):
        """
        返回 Django View处理方法
        使用 get_view_class 创建 AdminView 类，并且返回 view 方法，用于 get_urls 方法中

        :param admin_view_class: AdminView 类
        """
        return self.get_view_class(admin_view_class).as_view()

    def create_model_admin_view(self, admin_view_class, model, option_class):
        """
        使用 get_view_class 创建 ModelAdminView 类，并且返回 view 方法，用于 get_urls 方法中

        :param admin_view_class: AdminView 类，该类应该为 :class:`~xadmin.views.base.ModelAdminView` 的子类
        :param model: Model 类，目前该参数暂无作用
        :param option_class: Model 的 OptionClass，保存对该 Model 的相关定制
        """
        return self.get_view_class(admin_view_class, option_class).as_view()
    
    def gen_view(self, clz):
        def wrap(view, cacheable=False):
            '''
            url请求处理的起点，默认不做view缓存
            '''
            def wrapper(*args, **kwargs):
                return self.site_view_decor(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        return wrap(self.create_admin_view(clz))
    
    def gen_model_view(self, clz):
        model = getattr(clz, 'model')
        admin_class = self._registry[model]
        def wrap(view, cacheable=False):
            '''
            url请求处理的起点，默认不做view缓存
            '''
            def wrapper(*args, **kwargs):
                return self.site_view_decor(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        return wrap(self.create_model_admin_view(clz, model, admin_class))

    def get_urls(self):
        from django.conf.urls import patterns, url, include
        from xadmin.views.base import BaseView

        if settings.DEBUG:
            # 如果是DEBUG模式，检查依赖
            self.check_dependencies()

        #: 该方法主要用来使用 AdminSite.admin_view 封装 view
        def wrap(view, cacheable=False):
            '''
            url请求处理的起点，默认不做view缓存
            '''
            def wrapper(*args, **kwargs):
                return self.site_view_decor(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        # 添加 i18n_javascript view， 用于js的国际化
        urlpatterns = patterns('',
                               url(r'^jsi18n/$', wrap(self.i18n_javascript,
                                                      cacheable=True), name='jsi18n')
                               )

        # 添加注册的所有 AdminViewClass
        urlpatterns += patterns('',
                                *[url(
                                  path, wrap(self.create_admin_view(clz_or_func)) if type(clz_or_func) == type and issubclass(clz_or_func, BaseView) else include(clz_or_func(self)),
                                  name=name) for path, clz_or_func, name in self._registry_views]
                                )

        # 循环所有已注册的 Model, 逐一添加其ModelAdminViewClass
        for model, admin_class in self._registry.iteritems():
            view_urls = []
            app_label = model._meta.app_label
            module_name = model._meta.module_name
            for path, clz, name in self._registry_modelviews:
                view_attr_name = name.replace('%s_%s','view')
                name = name % (app_label, module_name)
                if hasattr(admin_class, view_attr_name):
                    view_class = getattr(admin_class, view_attr_name)
                    clz = view_class or clz
                m_view = wrap( self.create_model_admin_view(clz, model, admin_class) )
                view_urls.append( url(path, m_view, name=name) )
            urlpatterns += patterns('',
                                        url(
                                            r'^%s/%s/' % (app_label, module_name),
                                            include(patterns('', *view_urls))
                                        )
                                    )

        return urlpatterns

    @property
    def urls(self):
        """
        返回 xadmin site 的urls，用于设置django的urls。该方法用于属性使用。在您的Django的 ``urls.py`` 中，使用示例如下::

            from django.conf.urls import patterns, include, url

            import xadmin
            xadmin.autodiscover()

            urlpatterns = patterns('',
                url(r'', include(xadmin.site.urls)),
            )

        """
        return self.get_urls(), self.name, self.app_name

    def i18n_javascript(self, request):
        if settings.USE_I18N:
            from django.views.i18n import javascript_catalog
        else:
            from django.views.i18n import null_javascript_catalog as javascript_catalog
        return javascript_catalog(request, packages=['django.conf', 'xadmin'])
    
    def get_model_url(self, model, name, *args, **kwargs):
        """
        路径工具函数
        通过 model, name 取得 url，会自动拼成 urlname，并会加上 AdminSite.app_name 的 url namespace
        """
        return reverse(
            '%s:%s_%s_%s' % (self.app_name, model._meta.app_label,
                             model._meta.module_name, name),
            args=args, kwargs=kwargs, current_app=self.name)

    def url_for(self, name, *args, **kwargs):
        return reverse( '%s:%s'%(self.name, name) ,current_app=self.name)
        
    def get_model_perm(self, model, name):
        return '%s.%s_%s' % (model._meta.app_label, name, model._meta.module_name)
    
    def get_sys_menu(self):
        '''
        加载系统所有菜单
        '''
        for model, model_admin in self._registry.items():
            if getattr(model_admin, 'hide_menu', False) or getattr(model_admin, 'hidden_menu', False):
                continue
            if hasattr(model_admin, 'menu_group'):
                m_menu_group = model_admin.menu_group or '_default_group'
            else:
                m_menu_group = '_default_group'
            icon = getattr(model_admin,'model_icon', defs.DEFAULT_MODEL_ICON)
            
            app_label = getattr(model_admin, 'app_label', model._meta.app_label)  #model_admin.app_label
            model_dict = {
                'title': getattr(model_admin, 'verbose_name', '') or  unicode(capfirst(model._meta.verbose_name_plural)),
                'url': self.get_model_url(model, "changelist"),
                'icon': icon,
                'perm': self.get_model_perm(model, 'view'),
                'order': model_admin.order,
            }
            m_menu = self.sys_menu[app_label]
            if m_menu_group in m_menu.keys():
                m_menu[m_menu_group]['menus'].append(model_dict)
            else:
                m_menu['_default_group']['menus'].append(model_dict)
        
        for page in self._registry_pages:
            if getattr(page, 'hide_menu', False)or getattr(page, 'hidden_menu', False):
                continue
            if hasattr(page, 'menu_group'):
                m_menu_group = page.menu_group or '_default_group'
            else:
                m_menu_group = '_default_group'
            app_label = page.app_label
            model_dict = {
                'title': page.verbose_name,
                'url': page.get_page_url(),
                'icon': page.icon,
                'perm': 'auth.'+ (page.perm or 'not_setting_perm'),
                'order': page.order,
            }
            m_menu = self.sys_menu[app_label]
            if m_menu_group in m_menu.keys():
                m_menu[m_menu_group]['menus'].append(model_dict)
            else:
                m_menu['_default_group']['menus'].append(model_dict)
                
        for app_menu in self.sys_menu.values():
            for menu in app_menu.values():
                menu['menus'].sort(key=sortkeypicker(['order']))
        self.sys_menu_loaded = True
    
    def get_app_menu(self, app_label):
        '''
        获取某个APP的菜单
        '''
        if not self.sys_menu_loaded:self.get_sys_menu()
        m_menu = self.sys_menu[app_label]
        m_app = self.app_dict[app_label]
        ret = []
        if hasattr(m_app,'menus'):
            m_menus = m_app.menus
            for e in m_menus:
                ret.append(m_menu[e[0]])
        if len(m_menu['_default_group'])>0:
                ret.append(m_menu['_default_group'])
        return ret

    def get_menu(self):
        '''
        获取站点所有菜单
        '''
        if not self.sys_menu_loaded:self.get_sys_menu()
        ret = []
        for k,v in self.sys_menu.items():
            app_label = k
            m_menu = v
            m_app = self.app_dict[app_label]

            if hasattr(m_app,'menus'):
                m_menus = m_app.menus
                for e in m_menus:
                    ret.append(m_menu[e[0]])
            if len(m_menu['_default_group'])>0:
                    ret.append(m_menu['_default_group'])
        return ret
    
    def get_site_menu(self, select_app):
        '''
        获取APP列表菜单
        '''
        if not self.sys_menu_loaded:self.get_sys_menu()
        if self.show_default_index:
            ret = [{
                        'app_label': '',
                        'title': u'面板',
                        'url': self.url_for('index'),
                        'icon': '',
                        'selected': not select_app
                    }]
        else:
            ret = []
        for app_label,mod in self.app_dict.iteritems():
            if hasattr(mod,'verbose_name'):
                m_first_url = None
                if hasattr(mod,'index_url_name'):
                    m_first_url  = self.url_for(mod.index_url_name)
                else:
                    app_menu = self.sys_menu[app_label]
                    if hasattr(mod,'menus'):
                        m_groups = mod.menus
                        for e in m_groups:
                            m_menus = app_menu[e[0]]['menus']
                            if len(m_menus)>0:
                                m_first_url = m_menus[0]['url']
                                break
                    if not m_first_url:
                        d_menus = app_menu['_default_group']['menus']
                        if len(d_menus)>0:
                            m_first_url = d_menus[0]['url']
                        else:
                            m_first_url = '#'

                ret.append({
                            'app_label': app_label,
                            'title': getattr(mod,'verbose_name', unicode(capfirst(app_label))  ),
                            'url': m_first_url,
                            'icon': '',
                            'selected': app_label==select_app
                            })
                mod.index_url = m_first_url
        return ret
        

# AdminSite 的单例, 全站统一实例
site = AdminSite()
