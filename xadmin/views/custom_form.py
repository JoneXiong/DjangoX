# coding=utf-8

import json

import xadmin
from base import filter_hook
from form import FormView

from custom_page import PageView
from xadmin import options
from xadmin.dutils import JSONEncoder

    
class FormPage(FormView,PageView):
    
    @filter_hook
    def get_redirect_url(self):
        if self._has_file_field:
            return self.request.get_full_path()
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
    hide_menu = True
    icon = 'fa fa-tasks'
    
    @filter_hook
    def get_response(self):
        response = super(FormAction, self).get_response()
        if "_continue" not in self.param_list():
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
        
        
class ConfigFormPage(FormPage):
    
    key = None
    
    def get_initial_data(self):
        _db_data = options.options[self.key]
        if _db_data:
            return json.loads(_db_data)
        else:
            return {}

    @filter_hook
    def save_forms(self):
        forn_data = self.form_obj.cleaned_data
        db_data = json.dumps(forn_data, cls=JSONEncoder, ensure_ascii=False)
        options.options[self.key] = db_data

    @classmethod
    def options(cls, name):
        _db_data = options.options[cls.key]
        if _db_data:
            _dict =  json.loads(_db_data)
            return _dict.get(name, None)
        else:
            return None
        
