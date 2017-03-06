# coding=utf-8
from datetime import datetime

from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):

    user = models.OneToOneField(User, related_name='profile')
    mobile = models.CharField('手机号', max_length=64, blank=True, null=True)
    #image = models.ImageField(upload_to="image/%Y/%m", default="image/default.png")

    class Meta:
        app_label ='auth'
        db_table = 'auth_userprofile'
        verbose_name = u'用户信息'
        verbose_name_plural = verbose_name


class EmailVerifyRecord(models.Model):
    SEND_TYPE_CHOICE = (
        ('register', u'register'),
        ('forget', u'forget')
    )
    code = models.CharField(max_length=20, verbose_name=u'code')
    email = models.EmailField(max_length=50, verbose_name=u'email')
    send_type = models.CharField(max_length=10, choices=SEND_TYPE_CHOICE, default='forget')
    send_time = models.DateTimeField(default=datetime.now)

    def __unicode__(self):
        return '{0}({1})'.format(self.code, self.email)

    class Meta:
        verbose_name = u'Email验证码'
        verbose_name_plural = verbose_name
