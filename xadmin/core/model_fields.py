# coding=utf-8

import logging
import time
import hashlib
import random

from django.db import models
from django.utils.text import capfirst
from django.core import exceptions
from django.db.models import SlugField

from .form_fields import MultiSelectFormField


class AutoMD5SlugField(SlugField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank', True)

        populate_from = kwargs.pop('populate_from', None)
        if populate_from is None:
            logging.warning("missing 'populate_from' argument")
            self._populate_from = ''
        else:
            self._populate_from = populate_from

        self.hash_key = kwargs.pop('hash_key', time.time)
        super(AutoMD5SlugField, self).__init__(*args, **kwargs)

    def get_new_slug(self, model_instance, extra=''):
        slug_field = model_instance._meta.get_field(self.attname)

        if callable(self.hash_key):
            hash_key = self.hash_key()
        else:
            hash_key = self.hash_key
        slug = hashlib.md5('%s%s%s' % (hash_key, getattr(model_instance, self._populate_from), extra)).hexdigest()
        slug_len = slug_field.max_length
        if slug_len:
            slug = slug[:slug_len]

        return slug

    def create_slug(self, model_instance, add):
        # get fields to populate from and slug field to set
        slug = getattr(model_instance, self.attname)
        if slug:
            # slugify the original field content and set next step to 2
            return slug

        slug = self.get_new_slug(model_instance)

        # exclude the current model instance from the queryset used in finding
        # the next valid slug
        if hasattr(model_instance, 'gen_slug_queryset'):
            queryset = model_instance.gen_slug_queryset()
        else:
            queryset = model_instance.__class__._default_manager.all()
        if model_instance.pk:
            queryset = queryset.exclude(pk=model_instance.pk)

        kwargs = {}
        kwargs[self.attname] = slug

        while queryset.filter(**kwargs).count() > 0:
            slug = self.get_new_slug(model_instance, random.random())
            kwargs[self.attname] = slug

        return slug

    def pre_save(self, model_instance, add):
        value = unicode(self.create_slug(model_instance, add))
        setattr(model_instance, self.attname, value)
        return value

    def get_internal_type(self):
        return "SlugField"


class MultiSelectField(models.Field):
    __metaclass__ = models.SubfieldBase
 
    def get_internal_type(self):
        return "CharField"
 
    def get_choices_default(self):
        return self.get_choices(include_blank=False)
 
    def formfield(self, **kwargs):
        # don't call super, as that overrides default widget if it has choices
        defaults = {'required': not self.blank, 'label': capfirst(self.verbose_name),
                    'help_text': self.help_text, 'choices': self.choices}
        if self.has_default():
            defaults['initial'] = self.get_default()
        defaults.update(kwargs)
        return MultiSelectFormField(**defaults)
 
    def get_prep_value(self, value):
        return value
 
    def get_db_prep_value(self, value, connection=None, prepared=False):
        if isinstance(value, basestring):
            return value
        elif isinstance(value, list):
            return ",".join(value)
 
    def to_python(self, value):
        if value is not None:
            return value if isinstance(value, list) else value.split(',')
        return ''
 
    def contribute_to_class(self, cls, name):
        super(MultiSelectField, self).contribute_to_class(cls, name)
        if self.choices:
            func = lambda self, fieldname = name, choicedict = dict(self.choices): ",".join([choicedict.get(value, value) for value in getattr(self, fieldname)])
            setattr(cls, 'get_%s_display' % self.name, func)
 
    def validate(self, value, model_instance):
        arr_choices = self.get_choices_selected(self.get_choices_default())
        for opt_select in value:
            if (int(opt_select) not in arr_choices):  # the int() here is for comparing with integer choices
                raise exceptions.ValidationError(self.error_messages['invalid_choice'] % value)
        return
 
    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

class BetterCharField(models.Field):
    '''
    my_field = BetterCharField(25)
    '''
    def __init__(self, length, *args, **kwargs):
        self.length = length
        super(BetterCharField, self).__init__(*args, **kwargs)
    def db_type(self, connection):
        return 'char(%s)' % self.length


class CloudImageField(models.ImageField):
    
    def __init__(self, verbose_name=None, name=None, width_field=None,
            height_field=None, **kwargs):
        from .storage_qiniu import QiniuStorage
        kwargs['storage'] = QiniuStorage()
        super(CloudImageField, self).__init__(verbose_name, name, width_field, height_field, **kwargs)
   
# Fix south problems     
try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    add_introspection_rules([], ["^xadmin\.model_fields\.CloudImageField"])
