# coding=utf-8
import time

from django import forms
from django.views.generic import View
from django.http import HttpResponse, JsonResponse
from django.conf import settings

from xadmin import site
from xadmin.views.base import BaseView

class UploadView(BaseView):

    csrf = False

    def post(self, request, *args, **kwargs):
        callback = request.GET.get('CKEditorFuncNum')
        try:
            path = "uploads/" + time.strftime("%Y%m%d%H%M%S",time.localtime())
            f = request.FILES["upload"]

            from xadmin.core.storage_qiniu import save_imgs
            imgs = save_imgs([f])
            url = settings.REMOTE_MEDIA_URL + imgs[0]['img']

            #file_name = path + "_" + f.name
            #des_origin_f = open(file_name, "wb+")
            #for chunk in f.chunks():
            #    des_origin_f.write(chunk)
            #des_origin_f.close()
            #url = '/' + file_name
        except Exception, e:
            import traceback;traceback.print_exc()
        res = "<script>window.parent.CKEDITOR.tools.callFunction("+callback+",'"+url+"', '');</script>"
        return HttpResponse(res)
site.register_view(r'^ckupload/$', UploadView, name='ckupload')


class UploadDrogImgView(BaseView):
    csrf = False

    def post(self, request, *args, **kwargs):
        try:
            path = "uploads/" + time.strftime("%Y%m%d%H%M%S", time.localtime())
            file_dir_name = path.split('/')[-1]
            f = request.FILES["upload"]

            from xadmin.core.storage_qiniu import save_imgs
            imgs = save_imgs([f])
            url = settings.REMOTE_MEDIA_URL + imgs[0]['img']

            #file_name = path + "_" + f.name
            #with open(file_name, "wb+") as des_origin_f:
            #    for chunk in f.chunks():
            #        des_origin_f.write(chunk)
            #des_origin_f.close()
            #url = '/' + file_name
            success_message = {
                "uploaded": 1,
                "fileName": file_dir_name + "_" + f.name,
                "url": url
            }
            return JsonResponse(success_message)
        except:
            import traceback
            traceback.print_exc()
            fail_message = {
                "uploaded": 0,
                "error": {
                    "message": "上传失败"
                }
            }
            return JsonResponse(fail_message)

site.register_view(r'^ckupdrogload/$', UploadDrogImgView, name='ckupdrogupload')
