# coding=utf-8

from django import forms

import xadmin
from xadmin.views.action import Action, FormAction


from app import models

class MyAction1(Action):
    
    def action(self, qs):
        print 'do MyAction1'
        self.msg('执行成功', 'success')
        return '5555555'
    
class MyAction3(Action):
    
    def action(self, qs):
        pass
    
class MyAction4(Action):
    
    def action(self, qs):
        pass
    
class MyAction5(Action):
    
    def action(self, qs):
        pass
    
class MyAction6(Action):
    
    def action(self, qs):
        pass
        
class VerifyFailForm(forms.Form):
    reason = forms.CharField(label=u'原因' )
        
class MyAction2(FormAction):
    
    form = VerifyFailForm
    
    def action(self, qs):
        print 'do MyAction2'
        #self.msg('执行成功', 'success')

class BAdmin(object):
    actions = [MyAction1,MyAction3,MyAction4,MyAction5,MyAction6, MyAction2]
    list_display = ['id', 'name']
    list_gallery = True

xadmin.site.register(models.B, BAdmin)