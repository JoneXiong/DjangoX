# coding=utf-8

from django.db import models


class B(models.Model):
    name = models.CharField('名称', max_length=500)
    #img = models.ImageField('图片', upload_to='app')
    #img2 = models.ImageField('图片2', upload_to='app',width_field='img2_width',height_field='img2_height',null=True,blank=True)
    img2_width = models.IntegerField('图片2宽',null=True,blank=True)
    img2_height = models.IntegerField('图片2高',null=True,blank=True)
    
    class Meta:
        app_label = 'app'