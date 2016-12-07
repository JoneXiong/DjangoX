#  coding=utf-8

import json
import logging

import django
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Permission
from django.db.models.base import ModelBase
from django.utils import six

from dutils import JSONEncoder
from manager import ModelManager


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

class NewBase(ModelBase):
    pass

class ExtModel(object):
    @classmethod
    def merge_class(cls, target_cls):
        for k, v in target_cls.__dict__.items():
            if k.startswith('__'):
                continue
            if hasattr(cls, k):
                logging.warning("class %s has attr %s, but only warning", cls.__name__, k)
            setattr(cls, k, v)

class BaseModel(models.Model, ExtModel):
    objects = ModelManager()
    had_init_related_lookup = False

    class Meta:
        abstract = True

#models.Model = BaseModel

def add_view_permissions(sender, **kwargs):
    """
    This syncdb hooks takes care of adding a view permission too all our
    content types.
    """
    # for each of our content types
    for content_type in ContentType.objects.all():
        # build our permission slug
        codename = "view_%s" % content_type.model

        # if it doesn't exist..
        if not Permission.objects.filter(content_type=content_type, codename=codename):
            # add it
            Permission.objects.create(content_type=content_type,
                                      codename=codename,
                                      name="Can view %s" % content_type.name)
            #print "Added view permission for %s" % content_type.name

# check for all our view permissions after a syncdb
try:
    from django.db.models.signals import post_syncdb
    post_syncdb.connect(add_view_permissions)
except:
    pass

#################### 公共注入部分结束 ###################

class Bookmark(models.Model):
    title = models.CharField(_(u'Title'), max_length=128)
    user = models.ForeignKey(AUTH_USER_MODEL, verbose_name=_(u"user"), blank=True, null=True)
    url_name = models.CharField(_(u'Url Name'), max_length=64)
    content_type = models.ForeignKey(ContentType)
    query = models.CharField(_(u'Query String'), max_length=1000, blank=True)
    is_share = models.BooleanField(_(u'Is Shared'), default=False)

    @property
    def url(self):
        base_url = reverse(self.url_name)
        if self.query:
            base_url = base_url + '?' + self.query
        return base_url

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _(u'Bookmark')
        verbose_name_plural = _('Bookmarks')


class UserSettings(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, verbose_name=_(u"user"))
    key = models.CharField(_('Settings Key'), max_length=256)
    value = models.TextField(_('Settings Content'))

    def json_value(self):
        return json.loads(self.value)

    def set_json(self, obj):
        self.value = json.dumps(obj, cls=JSONEncoder, ensure_ascii=False)

    def __unicode__(self):
        return "%s %s" % (self.user, self.key)

    class Meta:
        verbose_name = _(u'User Setting')
        verbose_name_plural = _('User Settings')


class SystemSettings(models.Model):
    key = models.CharField(_('Settings Key'), max_length=256)
    value = models.TextField(_('Settings Content'))
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    def __unicode__(self):
        return self.key

    class Meta:
        verbose_name = u'系统设置'
        verbose_name_plural = u'系统设置'


class UserWidget(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, verbose_name=_(u"user"))
    page_id = models.CharField(_(u"Page"), max_length=256)
    widget_type = models.CharField(_(u"Widget Type"), max_length=50)
    value = models.TextField(_(u"Widget Params"))

    def get_value(self):
        value = json.loads(self.value)
        value['id'] = self.id
        value['type'] = self.widget_type
        return value

    def set_value(self, obj):
        self.value = json.dumps(obj, cls=JSONEncoder, ensure_ascii=False)

    def save(self, *args, **kwargs):
        created = self.pk is None
        super(UserWidget, self).save(*args, **kwargs)
        if created:
            try:
                portal_pos = UserSettings.objects.get(
                    user=self.user, key="dashboard:%s:pos" % self.page_id)
                portal_pos.value = "%s,%s" % (self.pk, portal_pos.value) if portal_pos.value else self.pk
                portal_pos.save()
            except Exception:
                pass

    def __unicode__(self):
        return "%s %s widget" % (self.user, self.widget_type)

    class Meta:
        verbose_name = _(u'User Widget')
        verbose_name_plural = _('User Widgets')
