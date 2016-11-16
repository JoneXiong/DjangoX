# -*- coding: utf-8 -*-

import re
from functools import partial

from .dunderkey import dunder_get, dunder_partition, undunder_keys, dunder_truncate


class QuerySet(object):
    """Provides an interface to filter data and select specific fields from the data

    :param data: an iterable of dicts

    """

    def __init__(self, data=None):
        self.data = (data==None and [] or data)

    def filter(self, *args, **kwargs):
        """Filters data using the lookup parameters

        Lookup parameters can be passed as,

          1. keyword arguments of type `field__lookuptype=value` 

                 >>> c.items.filter(language__contains='java')
              they are combined using logical the ``and`` operator

             For nested fields, double underscore can be used eg::

                 >>> data = [{'a': {'b': 3}}, {'a': {'b': 10}}]
                 >>> c = Collection(data)
                 >>> c.items.filter(a__b__gt=5)

          2. pos arguments of the type ``field__lookuptype=Q(...)``.
             combined using logical `or` or negated using
             `not`

                 >>> c.items.filter(Q(language__exact='Python')
                                    |
                                    Q(language__exact='Ruby')

        :param args   : ``Q`` objects
        :param kwargs : lookup parameters
        :rtype        : QuerySet

        """
        return self.__class__(filter_items(self.data, *args, **kwargs))

    def select(self, *args, **kwargs):
        """Selects specific fields of the data
            >>> c.items.select('framework', 'type')

        :param args   : field names to select
        :param kwargs : optional keyword args

        """
        flatten = kwargs.pop('flatten', False)
        f = dunder_truncate if flatten else undunder_keys
        result = (f(d) for d in include_keys(self.data, args))
        return self.__class__(result)

    def __iter__(self):
        for d in self.data:
            yield d
            
    def count(self):
        if not hasattr(self.data, '__len__'):
            self.data = list(self.data)
        return len(self.data)
    
    def __getitem__(self, k):
        if not hasattr(self.data, '__len__'):
            self.data = list(self.data)
        return self.data[k]
    
    def __len__(self):
        if not hasattr(self.data, '__len__'):
            self.data = list(self.data)
        return len(self.data)
    
    def get_slice(self, start, end):
        if self.data:
            return self.data[start:end]
        else:
            return []
        
    def verbose(self,key):
        return key
    
    def _clone(self, count=None):
        if self.data:
            return self.data[:count]
        else:
            return self.get_slice(0, count)

Collection = QuerySet


def filter_items(items, *args, **kwargs):
    """Filters an iterable using lookup parameters

    :param items  : iterable
    :param args   : ``Q`` objects
    :param kwargs : lookup parameters
    :rtype        : lazy iterable (generator)

    """
    q1 = list(args) if args is not None else []
    q2 = [Q(**kwargs)] if kwargs is not None else []
    lookup_groups = q1 + q2
    pred = lambda item: all(lg.evaluate(item) for lg in lookup_groups)
    return (item for item in items if pred(item))


def lookup(key, val, item):
    """Checks if key-val pair exists in item using various lookup types

    The lookup types are derived from the `key` and then used to check
    if the lookup holds true for the item::

        >>> lookup('request__url__exact', 'http://example.com', item)

    The above will return True if item['request']['url'] ==
    'http://example.com' else False

    :param key  : (str) that represents the field name to find
    :param val  : (mixed) object to match the value in the item against
    :param item : (dict)
    :rtype      : (boolean) True if field-val exists else False

    """
    init, last = dunder_partition(key)
    if last == 'exact':
        return dunder_get(item, init) == val
    elif last == 'neq':
        return dunder_get(item, init) != val
    elif last == 'contains':
        val = guard_str(val)
        return iff_not_none(dunder_get(item, init), lambda y: val in y)
    elif last == 'icontains':
        val = guard_str(val)
        return iff_not_none(dunder_get(item, init), lambda y: val.lower() in y.lower())
    elif last == 'in':
        val = guard_iter(val)
        return dunder_get(item, init) in val
    elif last == 'startswith':
        val = guard_str(val)
        return iff_not_none(dunder_get(item, init), lambda y: y.startswith(val))
    elif last == 'istartswith':
        val = guard_str(val)
        return iff_not_none(dunder_get(item, init), lambda y: y.lower().startswith(val.lower()))
    elif last == 'endswith':
        val = guard_str(val)
        return iff_not_none(dunder_get(item, init), lambda y: y.endswith(val))
    elif last == 'iendswith':
        val = guard_str(val)
        return iff_not_none(dunder_get(item, init), lambda y: y.lower().endswith(val.lower()))
    elif last == 'gt':
        return iff_not_none(dunder_get(item, init), lambda y: y > val)
    elif last == 'gte':
        return iff_not_none(dunder_get(item, init), lambda y: y >= val)
    elif last == 'lt':
        return iff_not_none(dunder_get(item, init), lambda y: y < val)
    elif last == 'lte':
        return iff_not_none(dunder_get(item, init), lambda y: y <= val)
    elif last == 'regex':
        return iff_not_none(dunder_get(item, init), lambda y: re.search(val, y) is not None)
    elif last == 'filter':
        val = guard_Q(val)
        result = guard_list(dunder_get(item, init))
        return len(list(filter_items(result, val))) > 0
    else:
        return dunder_get(item, key) == val


## Classes to compose compound lookups (Q object)

class LookupTreeElem(object):
    """Base class for a child in the lookup expression tree"""

    def __init__(self):
        self.negate = False

    def evaluate(self, item):
        raise NotImplementedError

    def __or__(self, other):
        node = LookupNode()
        node.op = 'or'
        node.add_child(self)
        node.add_child(other)
        return node

    def __and__(self, other):
        node = LookupNode()
        node.add_child(self)
        node.add_child(other)
        return node


class LookupNode(LookupTreeElem):
    """A node (element having children) in the lookup expression tree

    Typically it's any object composed of two ``Q`` objects eg::

        >>> Q(language__neq='Ruby') | Q(framework__startswith='S')
        >>> ~Q(language__exact='PHP')

    """

    def __init__(self):
        super(LookupNode, self).__init__()
        self.children = []
        self.op = 'and'

    def add_child(self, child):
        self.children.append(child)

    def evaluate(self, item):
        """Evaluates the expression represented by the object for the item

        :param item : (dict) item
        :rtype      : (boolean) whether lookup passed or failed

        """
        results = map(lambda x: x.evaluate(item), self.children)
        result = any(results) if self.op == 'or' else all(results)
        return not result if self.negate else result

    def __invert__(self):
        newnode = LookupNode()
        for c in self.children:
            newnode.add_child(c)
        newnode.negate = not self.negate
        return newnode


class LookupLeaf(LookupTreeElem):
    """Class for a leaf in the lookup expression tree"""

    def __init__(self, **kwargs):
        super(LookupLeaf, self).__init__()
        self.lookups = kwargs

    def evaluate(self, item):
        """Evaluates the expression represented by the object for the item

        :param item : (dict) item
        :rtype      : (boolean) whether lookup passed or failed

        """
        result = all(lookup(k, v, item) for k, v in self.lookups.items())
        return not result if self.negate else result

    def __invert__(self):
        newleaf = LookupLeaf(**self.lookups)
        newleaf.negate = not self.negate
        return newleaf


# alias LookupLeaf to Q
Q = LookupLeaf


## functions that work on the keys in a dict

def include_keys(items, fields):
    """Function to keep only specified fields in data

    Returns a list of dict with only the keys mentioned in the
    `fields` param::

        >>> include_keys(items, ['request__url', 'response__status'])

    :param items  : iterable of dicts
    :param fields : (list) fieldnames to keep
    :rtype        : lazy iterable

    """
    return (dict((f, dunder_get(item, f)) for f in fields) for item in items)


## Exceptions

class LookupyError(Exception):
    """Base exception class for all exceptions raised by lookupy"""
    pass


## utility functions

def iff(precond, val, f):
    """If and only if the precond is True

    Shortcut function for precond(val) and f(val). It is mainly used
    to create partial functions for commonly required preconditions

    :param precond : (function) represents the precondition
    :param val     : (mixed) value to which the functions are applied
    :param f       : (function) the actual function

    """
    return False if not precond(val) else f(val)

iff_not_none = partial(iff, lambda x: x is not None)


def guard_type(classinfo, val):
    if not isinstance(val, classinfo):
        raise LookupyError('Value not a {classinfo}'.format(classinfo=classinfo))
    return val

guard_str = partial(guard_type, str)
guard_list = partial(guard_type, list)
guard_Q = partial(guard_type, Q)

def guard_iter(val):
    try:
        iter(val)
    except TypeError:
        raise LookupyError('Value not an iterable')
    else:
        return val


if __name__ == '__main__':
    pass

