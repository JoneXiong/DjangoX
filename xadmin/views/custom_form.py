# coding=utf-8

import json

import xadmin
from base import filter_hook
from form import FormView

from custom_page import PageView

    
class FormPage(FormView,PageView):
    
    @filter_hook
    def get_redirect_url(self):
        return self.get_response()

    @classmethod  
    def render_btn(cls, _redirect=None):
        m_root = xadmin.ROOT_PATH_NAME and '/'+xadmin.ROOT_PATH_NAME or ''
        if _redirect:
            return '<a href="%s/page/%s/?_redirect=%s" class="btn btn-primary"><i class="%s"></i> %s</a>'%( m_root, cls.__name__.lower(), _redirect, cls.icon, cls.verbose_name )
        else:
            return '<a href="%s/page/%s/" class="btn btn-primary"><i class="%s"></i> %s</a>'%( m_root, cls.__name__.lower(), cls.icon, cls.verbose_name )
        

class FormAction(FormPage):
    
    template = 'xadmin/views/form_action.html'
    hidden_menu = True
    icon = 'fa fa-tasks'
    
    @filter_hook
    def get_response(self):
        response = super(FormAction, self).get_response()
        if "_continue" not in self.request.REQUEST:
            action_return_url = self.request.META['HTTP_REFERER']
            response.set_cookie("_action_return_url", action_return_url)
        return response
    
    @filter_hook
    def get_redirect_url(self):
        action_return_url = self.request.COOKIES["_action_return_url"]
        return action_return_url
    
    def get_id_list(self):
            ids = self.request.GET.get('ids')
            m_list = ids.split('||')
            import urllib
            return [ json.loads( urllib.unquote(e) ) for e in m_list]
    
    @classmethod  
    def render_bottom_btn(cls, _redirect=None):
        m_root = xadmin.ROOT_PATH_NAME and '/'+xadmin.ROOT_PATH_NAME or ''
        if _redirect:
            return '<a href="%s/page/%s/?_redirect=%s" class="btn btn-default" onclick="return $.do_form_action(this);"><i class="%s"></i> %s</a>'%( m_root, cls.__name__.lower(), _redirect, cls.icon, cls.verbose_name )
        else:
            return '<a href="%s/page/%s/" class="btn btn-default" onclick="return $.do_form_action(this);"><i class="%s"></i> %s</a>'%( m_root, cls.__name__.lower(), cls.icon, cls.verbose_name )