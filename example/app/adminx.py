# -*- coding: utf-8 -*-

import xadmin
from xadmin import views
from xadmin.views.dashboard import AppDashboard

from app import models


### 全局变量设置 ###
xadmin.site.site_title = 'DjangoX'
xadmin.site.site_footer = 'My Footer'
xadmin.site.head_fix = True
#xadmin.site.menu_style = 'default'


### 公共类默认值设置 ###
class BaseSetting(object):
    enable_themes = True
    use_bootswatch = False
xadmin.site.register(views.BaseView, BaseSetting)

class GlobalSetting(object):
    global_search_models = [models.Host, models.IDC]
xadmin.site.register(views.SiteView, GlobalSetting)


### 站点首页设置 ### 
class MainDashboard(object):
    widgets = [
        [
            {"type": "html", "title": "Test Widget", "content": "<h3> Welcome to DjangoX! </h3><p>Join us: <br/>Github : https://github.com/JoneXiong/DjangoX</p>"},
            {"type": "chart", "model": "app.accessrecord", 'chart': 'user_count', 'params': {'_p_date__gte': '2013-01-08', 'p': 1, '_p_date__lt': '2013-01-29'}},
            {"type": "list", "model": "app.host", 'params': {'o':'-guarantee_date'}},
        ],
        [
            {"type": "qbutton", "title": "Quick Start", "btns": [{'model': models.Host}, {'model': models.IDC}, {'title': "DjangoX", 'url': "https://github.com/JoneXiong/DjangoX"}]},
            {"type": "addform", "model": models.MaintainLog},
        ]
    ]
xadmin.site.register(views.website.IndexView, MainDashboard)


### 各 App 默认首页设置 ###
class AppIndex(AppDashboard):
    app_label = 'app'
xadmin.site.register_appindex(AppIndex) # 如果没设定 appindex 则点击时自动进入第一菜单的页面

class AuthIndex(AppDashboard):
    app_label = 'xadmin'
    widget_customiz = False
xadmin.site.register_appindex(AuthIndex)


### 加载子层 ###
import admins
import pages
# import route
# import test_view
# import test_page
