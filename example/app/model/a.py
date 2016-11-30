# coding=utf-8

from django.db import models
from xadmin.models import BaseModel

class A(BaseModel):
    name = models.CharField('名称', max_length=500)
    b = models.ForeignKey('app.B', verbose_name="属主")
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        app_label = 'app'
