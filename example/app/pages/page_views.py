# coding=utf-8

from django.utils.safestring import mark_safe
import xadmin
from xadmin.views.page import PageView

class TestPage1(PageView):
    '''
    基本page页
    '''
    verbose_name = u'PageView1'
    app_label = 'app'
    menu_group = 'test_group'
    icon = "fa fa-circle"

    def get_content(self):
        return 'OK'
xadmin.site.register_page(TestPage1)


class TestPage2(PageView):
    '''
    带ajax页链接
    '''
    verbose_name = u'PageView2'
    app_label = 'app'
    menu_group = 'test_group'

    def get_media(self):
        media = self.vendor('xadmin.plugin.quick-form.js', 'xadmin.form.css')
        return media

    def get_content(self):
        return mark_safe('<a data-refresh-url="/xadmin/page/testpage2/" href="/xadmin/page/formpage1" class="ajaxform-handler" title="测试AjaxForm">GO</a>')
xadmin.site.register_page(TestPage2)

class TestPage3(PageView):
    '''
    bootstrap常用html
    '''
    verbose_name = u'PageView3'
    app_label = 'app'
    menu_group = 'test_group'
    template = 'bootstrap.html'

xadmin.site.register_page(TestPage3)
