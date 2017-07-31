# coding=utf-8

from xadmin import site
from xadmin.views.base import BaseView


class TestHTTPView(BaseView):
    '''
    最基础的 http 请求: 访问 /xadmin/test_view 查看
    '''

    def get(self, request, *args, **kwargs):
        return self.render_text('OK')
site.register_view(r'^test_view$', TestHTTPView, name='TestHTTPView')

