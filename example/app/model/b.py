# coding=utf-8

from django.db import models


class B(models.Model):
    name = models.CharField('名称', max_length=500)
    
    class Meta:
        app_label = 'app'