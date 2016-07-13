# coding=utf-8

from django.db import models

from xadmin.core.model_fields import CloudImageField

class TestImg(models.Model):
    
    img = CloudImageField('图片', upload_to='app', null=True)
    
    img2 = models.ImageField('图片2', upload_to='app',width_field='img2_width',height_field='img2_height',null=True,blank=True)
    img2_width = models.IntegerField('图片2宽',null=True,blank=True)
    img2_height = models.IntegerField('图片2高',null=True,blank=True)
    
    class Meta:
        app_label = 'app'