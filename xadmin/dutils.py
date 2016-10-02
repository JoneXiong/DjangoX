# coding=utf-8

import datetime
import decimal

import django
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import smart_unicode
from django.db.models.base import ModelBase


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
            
if django.VERSION[1] >= 8:
    from django.db.models.fields.related import ForeignObjectRel
    RelatedObject = ForeignObjectRel
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
    
try:
    from django.db import transaction
    commit_on_success = transaction.commit_on_success
except:
    from django.db import transaction
    commit_on_success = transaction.atomic
    
try:
    from django.core.cache import get_cache
except:
    def get_cache(k):
        from django.core.cache import caches
        return caches[k]
    
try:
    from django.contrib.contenttypes.generic import BaseGenericInlineFormSet, generic_inlineformset_factory
except:
    from django.contrib.contenttypes.forms import BaseGenericInlineFormSet, generic_inlineformset_factory
    
from django.core.mail import send_mail # use: send_mail(subject, email, from_email, [user.email])
