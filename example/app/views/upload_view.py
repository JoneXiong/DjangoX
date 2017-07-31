# coding=utf-8
import time

from django import forms
from django.views.generic import View
from django.http import HttpResponse

from xadmin import site
from xadmin.views.base import BaseView

class UploadView(BaseView):

    csrf = False

    def post(self, request, *args, **kwargs):
        callback = request.GET.get('CKEditorFuncNum')
        try:
            path = "static/upload/" + time.strftime("%Y%m%d%H%M%S",time.localtime())
            f = request.FILES["upload"]
            file_name = path + "_" + f.name
            des_origin_f = open(file_name, "wb+")
            for chunk in f.chunks():
                des_origin_f.write(chunk)
            des_origin_f.close()
        except Exception, e:
            import traceback;traceback.print_exc()
        res = "<script>window.parent.CKEDITOR.tools.callFunction("+callback+",'/"+file_name+"', '');</script>"
        return HttpResponse(res)
site.register_view(r'^ckupload/$', UploadView, name='ckupload')

