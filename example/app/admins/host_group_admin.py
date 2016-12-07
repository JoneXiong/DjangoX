# coding=utf-8

from django.http import HttpResponse
import xadmin
from xadmin import views
from xadmin.plugins.actions import BaseActionView

from app import models

class MyAction(views.Action):

    verbose_name = '操作1'
    model_perm = 'HostGroup_MyAction'

    # 而后实现 do_action 方法
    def do_action(self, queryset):
        # queryset 是包含了已经选择的数据的 queryset
        for obj in queryset:
            print 'do action for ',obj,type(obj)

        self.msg('操作成功', 'success')
        # 返回 HttpResponse
        #return HttpResponse('ok')    


class HostGroupAdd(views.CreateAdminView):

    def _get_response(self):
        return self.render_text('ok')
        #return HttpResponse('ok')

class HostGroupAdmin(object):
    list_display = ('name', 'description')
    list_display_links = ('name', 'description')
    list_display_links_details = True
    list_per_page = 5
    list_editable = ('name','description')

    search_fields = ['name']
    style_fields = {'hosts': 'checkbox-inline'}

    view_changelist = None
    view_add = HostGroupAdd
    view_delete = None
    view_detail = None
    view_dashboard = None
    actions = [MyAction, ]

    def do_patch(self):
        print 'do patch begin.'
        print dir(self.patch_form)
        print self.patch_form.fields
        print self.patch_form.cleaned_data
        super(HostGroupAdmin,self).do_patch()
        print 'do patch end.'

xadmin.site.register(models.HostGroup, HostGroupAdmin)
