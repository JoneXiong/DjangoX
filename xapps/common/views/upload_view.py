# coding=utf-8
import time

from django import forms
from django.views.generic import View

from xadmin import site
from xadmin.views.base import BaseView

class UploadView(BaseView):

    csrf = False

    def post(self, request, *args, **kwargs):
        callback = request.GET.get('CKEditorFuncNum')
        try:
            path = "uploads/" + time.strftime("%Y%m%d%H%M%S",time.localtime())
            f = request.FILES["upload"]
            file_name = path + "_" + f.name
            des_origin_f = open(file_name, "wb+")
            for chunk in f.chunks():
                des_origin_f.write(chunk)
            des_origin_f.close()
        except Exception, e:
            import traceback;traceback.print_exc()
        res = "<script>window.parent.CKEDITOR.tools.callFunction("+callback+",'/"+file_name+"', '');</script>"
        return self.render_text(res)
site.register_view(r'^ckupload/$', UploadView, name='ckupload')


class UploadDrogImgView(BaseView):
    csrf = False

    def post(self, request, *args, **kwargs):
        try:
            path = "uploads/" + time.strftime("%Y%m%d%H%M%S", time.localtime())
            file_dir_name = path.split('/')[-1]
            f = request.FILES["upload"]
            file_name = path + "_" + f.name
            with open(file_name, "wb+") as des_origin_f:
                for chunk in f.chunks():
                    des_origin_f.write(chunk)
            des_origin_f.close()
            success_message = {
                "uploaded": 1,
                "fileName": file_dir_name + "_" + f.name,
                "url": '/' + file_name
            }
            return self.render_json(success_message)
        except:
            import traceback
            traceback.print_exc()
            fail_message = {
                "uploaded": 0,
                "error": {
                    "message": "上传失败"
                }
            }
            return self.render_json(fail_message)

site.register_view(r'^ckupdrogload/$', UploadDrogImgView, name='ckupdrogupload')
