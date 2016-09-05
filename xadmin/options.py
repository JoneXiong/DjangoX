# coding=utf-8

from django.core.exceptions import ObjectDoesNotExist

from xadmin.models import SystemSettings

class OptionClass(object):
        _cache = {}
        
        def __init__(self):
            pass
        
        def __getitem__(self, key):
            item = key
            if item in self._cache:
                return self._cache[item]
            else:
                try:
                    opt = SystemSettings.objects.get(key=key)
                    value = opt.value
                except ObjectDoesNotExist:
                    value = None
                self._cache[item] = value
                return value
            
        def __setitem__(self, key, value):
            item = key
            if self.__getitem__(item) == value:
                return
            try:
                opt = SystemSettings.objects.get(key=key)
            except ObjectDoesNotExist:
                opt = SystemSettings(key=key)
            opt.value = value
            opt.save()
            self._cache[item] = value
            return opt
        
options = OptionClass()