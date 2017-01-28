# coding=utf-8

from django.utils.safestring import mark_safe
import xadmin
from xadmin.views.page import PageView

class TestPage1(PageView):
    verbose_name = u'PageView1(基本)'
    app_label = 'app'
    menu_group = 'test_group'
    icon = "fa fa-circle"

    def get_content(self):
        return 'OK'

xadmin.site.register_page(TestPage1)


class TestPage2(PageView):
    verbose_name = u'PageView2(带ajax页链接)'
    app_label = 'app'
    menu_group = 'test_group'
    
    def get_media(self):
        media = self.vendor('xadmin.plugin.quick-form.js', 'xadmin.form.css')
        return media
    
    def get_content(self):
        return mark_safe('<a data-refresh-url="/xadmin/page/testpage2/" href="/xadmin/page/formpage1" class="ajaxform-handler" title="测试AjaxForm">GO</a>') 
xadmin.site.register_page(TestPage2)

class TestPage3(PageView):
    verbose_name = u'PageView3(bootstrap常用)'
    app_label = 'app'
    menu_group = 'test_group'
    template = 'bootstrap.html'
    
xadmin.site.register_page(TestPage3)