# coding=utf-8

from .structs import SortedDict

class ConstType(type):
    def __new__(cls, name, bases, attrs):
        attrs_value = {}
        attrs_label = {}
        new_attrs = {}
        labels_to_values = {}

        for k, v in attrs.items():
            if k.startswith('__'):
                continue
            if isinstance(v, tuple):
                attrs_value[k] = v[0]
                attrs_label[k] = v[1]
                new_attrs[v[0]] = v[1]
                labels_to_values[v[1]] = v[0]
            elif isinstance(v, dict) and 'label' in v:
                attrs_value[k] = v['value']
                attrs_label[k] = v['label']
                labels_to_values[v['label']] = v['value']
                new_attrs[v['value']] = v['label']
            else:
                attrs_value[k] = v
                attrs_label[k] = v

        sort_new_attrs = sorted(new_attrs.iteritems(), key=lambda (k, v): k)
        new_attrs = SortedDict(sort_new_attrs)

        obj = type.__new__(cls, name, bases, attrs_value)
        obj.values = attrs_value
        obj.labels = attrs_label
        obj.labels_to_values = labels_to_values
        obj.attrs = new_attrs
        return obj


class Const(object):
    __metaclass__ = ConstType
