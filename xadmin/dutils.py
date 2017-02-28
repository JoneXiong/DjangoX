# coding=utf-8

import datetime
import decimal

import django
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import smart_unicode
from django.db.models.base import ModelBase
from django.template import loader
from django.template.context import RequestContext


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

if django.VERSION[1] >= 8:
    from django.apps import apps
    get_model = apps.get_model
else:
    from django.db.models import get_model


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


from django.core.mail import send_mail # use: send_mail(subject, email, from_email, [user.email])

if django.VERSION[1] >= 8:
    from django.utils.module_loading import import_module
    from django.forms.utils import flatatt
    from django.forms.utils import ErrorDict
    from django.forms.utils import ErrorList
    from django.contrib.contenttypes.forms import BaseGenericInlineFormSet, generic_inlineformset_factory
else:
    from django.utils.importlib import import_module
    from django.forms.util import flatatt
    from django.forms.util import ErrorDict
    from django.forms.util import ErrorList
    from django.contrib.contenttypes.generic import BaseGenericInlineFormSet, generic_inlineformset_factory


def render_to_string(tpl, context_instance=None):
    if django.VERSION[1]>=8:
        return loader.render_to_string(tpl, context=get_context_dict(context_instance))
    else:
        return loader.render_to_string(tpl, context_instance=context_instance)


def get_context_dict(context):
    """
     Contexts in django version 1.9+ must be dictionaries. As xadmin has a legacy with older versions of django,
    the function helps the transition by converting the [RequestContext] object to the dictionary when necessary.
    :param context: RequestContext
    :return: dict
    """
    if isinstance(context, RequestContext):
        ctx = {}
        map(ctx.update, context.dicts)
    else:
        ctx = context
    return ctx
