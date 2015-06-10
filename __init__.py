# -*- coding: utf-8 -*-

from xadmin.sites import site

VERSION = [0,5,0]

ROOT_PATH_NAME = ''
verbose_name = u'系统'

menus = (
         ('auth_group', u'权限',  'auth_icon'),
         )


def autodiscover():
    """
    Auto-discover INSTALLED_APPS admin.py modules and fail silently when
    not present. This forces an import on them to register any admin bits they
    may want.
    """

    from django.conf import settings
    from django.utils.importlib import import_module
    from django.utils.module_loading import module_has_submodule

    # 为 crispy_form 动态设置的settings项
    setattr(settings, 'CRISPY_TEMPLATE_PACK', 'bootstrap3')
    setattr(settings, 'CRISPY_CLASS_CONVERTERS', {
        "textinput": "textinput textInput form-control",
        "fileinput": "fileinput fileUpload form-control",
        "passwordinput": "textinput textInput form-control",
    })
    # 加载内置相关视图
    from xadmin.views import register_builtin_views
    register_builtin_views(site)

    # 加载插件
    from xadmin.plugins import register_builtin_plugins
    register_builtin_plugins(site)

    # 加载各app的 adminx
    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        
        app_label = app.split('.')[-1]
        site.app_dict[app_label] = mod
        
        # app级菜单初始化
        site.sys_menu[app_label] = {'_default_group':{'title': u'其他', 'icon': 'group_configure', 'menus': []}  }
        if hasattr(mod,'menus'):
            m_menus = mod.menus
            for e in m_menus:
                site.sys_menu[app_label][e[0]] = {'title': e[1], 'icon': e[2], 'menus': []}
        
        # 导入 adminx 模块
        try:
            before_import_registry = site.copy_registry()
            import_module('%s.adminx' % app)
        except:
            # Reset the model registry to the state before the last import as
            # this import will have to reoccur on the next request and this
            # could raise NotRegistered and AlreadyRegistered exceptions
            # (see #8245).
            site.restore_registry(before_import_registry)

            # Decide whether to bubble up this error. If the app just
            # doesn't have an admin module, we can ignore the error
            # attempting to import it, otherwise we want it to bubble up.
            if module_has_submodule(mod, 'adminx'):
                raise