#  coding=utf-8

from django.db import models
from django.db.models.query import QuerySet
from django.core.exceptions import ObjectDoesNotExist

class CustomQuerySet(QuerySet):

    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except ObjectDoesNotExist:
            return None

    def get_first(self, *args, **kwargs):
        objs = list(self.filter(*args, **kwargs)[:1])
        if not objs:
            return None
        return objs[0]

class ModelManager(models.Manager):

    def get_query_set(self):
        return CustomQuerySet(self.model, using=self._db)

    def get_or_none(self, **kwargs):
        return self.get_query_set().get_or_none(**kwargs)

    def get_first(self, *args, **kwargs):
        return self.get_query_set().get_first()
