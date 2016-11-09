# coding=utf-8

from django.core.exceptions import PermissionDenied

import xadmin
from base import SiteView, filter_hook


class PageView(SiteView):
    verbose_name = None
    template = 'xadmin/views/page.html'
    
    app_label = 'xadmin'
    menu_group = '_default_group'
    icon = 'fa fa-cog'
    order = 0
    
    hide_menu = False
    perm = None#'comm_page_code'
    pop = False
    
    def init_request(self, *args, **kwargs):
        u'''
        类实例化时执行
        '''
        #if not self.perm:
        #   self.perm = self.__class__.__name__
        perm_code = self.perm or 'not_setting_perm'
        if self.need_site_permission and not self.user.has_perm('auth.'+perm_code):
            raise PermissionDenied
        if '_pop' in self.request.GET or 'pop' in self.request.GET:
            self.pop = True
            self.base_template = 'xadmin/base_pure.html'
    
    def get(self, request, *args, **kwargs):
        u'''
        Django http GET请求的返回
        '''
        return self.render_tpl(self.template, self.get_context())
    
    def get_content(self):
        u'''
        页面主体内容
        '''
        pass
    
    @filter_hook
    def get_context(self):
        u'''
        返回上下文
        '''
        context = super(PageView, self).get_context()
        context.update({
                        'content': self.get_content() or '',
                        'title': self.verbose_name or self.__class__.__bases__ [0].__name__,
                        })
        return context
    
    @classmethod 
    def get_page_url(cls):
        m_root = xadmin.ROOT_PATH_NAME and '/'+xadmin.ROOT_PATH_NAME or ''
        return '%s/page/%s/'%(m_root, cls.__name__.lower())
    
    @filter_hook
    def get_breadcrumb(self):
        bcs = super(PageView, self).get_breadcrumb()
        bcs.append({'title': self.verbose_name or self.__class__.__bases__ [1].__name__})
        return bcs
