# coding=utf-8

import xadmin
from xadmin.views import ModelAdminView


class TestModelAdminView(ModelAdminView):
    
    def get(self, request, obj_id):
        return self.render_text('OK')

xadmin.site.register_modelview(r'^(.+)/test/$', TestModelAdminView, name='%s_%s_test')