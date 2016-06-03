# coding=utf-8

import xadmin
from xadmin.views.base import BaseView
from django.http import HttpResponseRedirect


class TestHTTPView(BaseView):

    def get(self, request, *args, **kwargs):
        return self.render_text('OK') 
xadmin.site.register_view(r'^test_view$', TestHTTPView, name='TestHTTPView')

class TestImg(BaseView):

    def get(self, request, *args, **kwargs):
        return self.render_text('<img src="/abc.jpg?url=abc"  style="display:none;"></img>') 
xadmin.site.register_view(r'^test_img$', TestImg, name='TestImg')

class TestImgRedirect(BaseView):
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect('http://xxx.qiniucdn.com/FnBqr6pIt1pdXJyxcNPwH2WdmSO7')

xadmin.site.register_view(r'^abc.jpg$', TestImgRedirect, name='TestImgRedirect')


from xadmin.views.website import IndexView
xadmin.site.register_view(r'^test_index$', IndexView, name='TestHTTPView')


