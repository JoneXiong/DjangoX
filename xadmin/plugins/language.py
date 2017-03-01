
from django.conf import settings
from django.template import loader, RequestContext

from xadmin.sites import site
from xadmin.views import BasePlugin, SiteView
from xadmin import dutils


class SetLangNavPlugin(BasePlugin):

    def block_top_navmenu(self, context, nodes):
        _context = RequestContext(self.request)
        _context.update({
                'redirect_to': self.request.get_full_path(),
            })
        nodes.append(
            dutils.render_to_string('xadmin/blocks/comm.top.setlang.html', context_instance=_context))

if settings.LANGUAGES and 'django.middleware.locale.LocaleMiddleware' in settings.MIDDLEWARE_CLASSES:
    site.register_plugin(SetLangNavPlugin, SiteView)
    site.register_view(r'^i18n/', lambda site: 'django.conf.urls.i18n', 'i18n')
