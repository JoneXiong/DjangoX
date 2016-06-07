# coding=utf-8

import datetime
import decimal

import django
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import smart_unicode
from django.db.models.base import ModelBase
from django.db.models.fields.related import RelatedField


class JSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.date):
            return o.strftime('%Y-%m-%d')
        elif isinstance(o, datetime.datetime):
            return o.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(o, decimal.Decimal):
            return str(o)
        elif isinstance(o, ModelBase):
            return '%s.%s' % (o._meta.app_label, o._meta.module_name)
        else:
            try:
                return super(JSONEncoder, self).default(o)
            except Exception:
                return smart_unicode(o)
            
if django.VERSION[1] > 8:
    RelatedObject = RelatedField
else:
    from django.db.models.related import RelatedObject
    RelatedObject = RelatedObject
    
try:
    from django.db.models import get_model
except:
    from django.apps import apps
    get_model = apps.get_model


try:
    from django.forms.util import flatatt
except:
    from django.forms.utils import flatatt
    
try:
    from django.forms.util import ErrorDict
except:
    from django.forms.utils import ErrorDict
    
try:
    from django.forms.util import ErrorList
except:
    from django.forms.utils import ErrorList