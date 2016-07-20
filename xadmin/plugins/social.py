# coding=utf-8

from django.template import loader
from django.conf import settings

from xadmin.views.base import BasePlugin
from xadmin.sites import site
from xadmin.views.website import LoginView


class SocialLoginPlugin(BasePlugin):
    
    def init_request(self, *args, **kwargs):
        return getattr(settings, 'XADMIN_SOCIAL_ENABLE', False)
    
    def get_media(self, media):
        media = media + self.vendor('xadmin.plugins.social.css')
        return media

    def block_form_bottom(self, context, nodes):
        _tpl = 'xadmin/auth/login_social_block.html'
        nodes.append(loader.render_to_string(_tpl, context_instance=context))

site.register_plugin(SocialLoginPlugin, LoginView)