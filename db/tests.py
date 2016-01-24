"""
   lookupy.tests
   ~~~~~~~~~~~~~

   This module contains tests for the lookupy module written using
   nose to be run using::

       $ nosetests -v

"""

import re
from nose.tools import assert_list_equal, assert_equal, assert_raises

from .query import filter_items, lookup, include_keys, Q, QuerySet, \
    Collection, LookupyError
from .dunderkey import dunderkey, dunder_partition, dunder_init, dunder_last, \
    dunder_get, undunder_keys, dunder_truncate


entries_fixtures = [{'request': {'url': 'http://example.com', 'headers': [{'name': 'Connection', 'value': 'Keep-Alive'}]},
                     'response': {'status': 404, 'headers': [{'name': 'Date', 'value': 'Thu, 13 Jun 2013 06:43:14 GMT'},
                                                             {'name': 'Content-Type', 'value': 'text/html'}]}},
                    {'request': {'url': 'http://example.org', 'headers': [{'name': 'Connection', 'value': 'Keep-Alive'}]},
                     'response': {'status': 200, 'headers': [{'name': 'Date', 'value': 'Thu, 13 Jun 2013 06:43:14 GMT'},
                                                             {'name': 'Content-Type', 'value': 'text/html'}]}},
                    {'request': {'url': 'http://example.com/myphoto.jpg', 'headers': [{'name': 'Connection', 'value': 'Keep-Alive'}]},
                     'response': {'status': 200, 'headers': [{'name': 'Date', 'value': 'Thu, 13 Jun 2013 06:43:14 GMT'},
                                                             {'name': 'Content-Type', 'value': 'image/jpg'}]}}]


def fe(entries, *args, **kwargs):
    return list(filter_items(entries, *args, **kwargs))


def ik(entries, fields):
    return list(include_keys(entries, fields))


## Tests




def test_Collection():
    c = Collection(entries_fixtures)
    assert_list_equal(list(c), entries_fixtures)
    assert_list_equal(list(c), entries_fixtures)


def test_Q():
    entries = entries_fixtures
    q1 = Q(response__status__exact=404, request__url__contains='.com')
    assert q1.evaluate(entries[0])

    # test with negation
    q2 = ~Q(response__status__exact=404)
    assert q2.evaluate(entries[1])
    # test multiple application of negation
    assert not (~q2).evaluate(entries[1])

    q3 = Q(response__status=200)
    assert not (q1 & q3).evaluate(entries[0])
    assert (q1 | q3).evaluate(entries[0])
    assert (~(q1 & q3)).evaluate(entries[0])

    assert_list_equal(list(((Q(request__url__endswith='.jpg') | Q(response__status=404)).evaluate(e)
                      for e in entries)),
                      [True, False, True])

    assert_list_equal(list(((~Q(request__url__endswith='.jpg') | Q(response__status=404)).evaluate(e)
                      for e in entries)),
                      [True, True, False])


def test_lookup():
    entry1, entry2, entry3 = entries_fixtures
    # exact       -- works for strings and int
    assert lookup('request__url__exact', 'http://example.com', entry1)
    assert not lookup('request_url__exact', 'http://example.org', entry1)
    assert lookup('response__status__exact', 404, entry1)
    assert not lookup('response__status__exact', 404, entry2)
    assert lookup('response_unknown__exact', None, entry1)

    # neq         -- works for strings and ints
    assert not lookup('request__url__neq', 'http://example.com', entry1)
    assert lookup('request_url__neq', 'http://example.org', entry1)
    assert not lookup('response__status__neq', 404, entry1)
    assert lookup('response__status__neq', 404, entry2)
    assert not lookup('response_unknown__neq', None, entry1)

    # contains    -- works for strings, else raises error
    assert lookup('request__url__contains', '.com', entry1)
    assert not lookup('request__url__contains', 'www', entry1)
    assert_raises(LookupyError, lookup, 'response__status__contains',
                  2, entry2)
    assert_raises(LookupyError, lookup, 'response__unknown__contains',
                  None, entry2)

    # icontains   -- works for strings, else raises error
    assert lookup('request__url__icontains', 'EXAMPLE', entry1)
    assert not lookup('request__url__icontains', 'www', entry1)
    assert_raises(LookupyError, lookup, 'response__status__icontains',
                  2, entry2)
    assert_raises(LookupyError, lookup,
                  'response__unknown__icontains', None, entry2)

    # in          -- works for strings and lists, else raises error
    assert lookup('request__url__in', ['http://example.com',
                                       'http://blog.example.com'], entry1)

    assert lookup('response__status__in', [400, 200], entry2)
    assert not lookup('response__status__in', [], entry2)
    assert lookup('request__url__in', 'http://example.com/?q=hello', entry1)
    assert_raises(LookupyError, lookup, 'response__status__in', 404, entry1)

    # startswith  -- works for strings, else raises error
    assert lookup('request__url__startswith', 'http://', entry1)
    assert not lookup('request__url__startswith', 'HTTP://', entry1)
    assert_raises(LookupyError, lookup,
                  'response__status__startswith', 4, entry1)

    # istartswith -- works for strings, else raises error
    assert lookup('request__url__istartswith', 'http://', entry1)
    assert lookup('request__url__istartswith', 'HTTP://', entry1)
    assert_raises(LookupyError, lookup,
                  'response__status__istartswith', 4, entry1)

    # endswith    -- works for strings, else raises error
    assert lookup('request__url__endswith', '.jpg', entry3)
    assert not lookup('request__url__endswith', '.JPG', entry3)
    assert_raises(LookupyError, lookup, 'response__status__endswith',
                  0, entry3)

    # iendswith   -- works for strings, else raises error
    assert lookup('request__url__iendswith', '.jpg', entry3)
    assert lookup('request__url__iendswith', '.JPG', entry3)
    assert_raises(LookupyError, lookup, 'response__status__iendswith',
                  0, entry3)

    # gt          -- works for strings and int
    assert lookup('response__status__gt', 200, entry1)
    assert not lookup('response__status__gt', 404, entry1)
    assert lookup('request__url__gt', 'ftp://example.com', entry1)
    assert not lookup('request__url__gt', 'http://example.com', entry1)

    # gte         -- works for strings and int
    assert lookup('response__status__gte', 200, entry1)
    assert lookup('response__status__gte', 404, entry1)
    assert lookup('request__url__gte', 'ftp://example.com', entry1)
    assert lookup('request__url__gte', 'http://example.com', entry1)

    # lt          -- works for strings and int
    assert lookup('response__status__lt', 301, entry2)
    assert not lookup('response__status__lt', 200, entry2)
    assert lookup('request__url__lt', 'ws://example.com', entry2)
    assert not lookup('request__url__lt', 'http://example.org', entry2)

    # lte         -- works for strings and int
    assert lookup('response__status__lte', 301, entry2)
    assert lookup('response__status__lte', 200, entry2)
    assert lookup('request__url__lte', 'ws://example.com', entry2)
    assert lookup('request__url__lte', 'http://example.org', entry2)

    # regex       -- works for compiled patterns and strings
    pattern = r'^http:\/\/.+g$'
    assert lookup('request__url__regex', pattern, entry2)
    assert lookup('request__url__regex', pattern, entry3)
    assert not lookup('request__url__regex', pattern, entry1)
    compiled_pattern = re.compile(pattern)
    assert lookup('request__url__regex', compiled_pattern, entry2)
    assert lookup('request__url__regex', compiled_pattern, entry3)
    assert not lookup('request__url__regex', compiled_pattern, entry1)

    # filter      -- works for Q objects, else raises error
    assert lookup('response__headers__filter',
                  Q(name__exact='Content-Type', value__exact='image/jpg'),
                  entry3)
    assert not lookup('response__headers__filter',
                      Q(name__exact='Content-Type', value__exact='text/html'),
                      entry3)
    assert_raises(LookupyError, lookup, 'response__headers__filter',
                  0, entry3)
    assert_raises(LookupyError, lookup, 'response__headers__filter',
                  "hello", entry3)
    assert_raises(LookupyError, lookup, 'response__headers__filter',
                  None, entry3)
    assert_raises(LookupyError, lookup, 'response__headers__filter',
                  {'a': 'b'}, entry3)
    assert_raises(LookupyError, lookup, 'response__status__filter',
                  Q(name__exact='Content-Type', value__exact='image/jpg'),
                  entry3)

    # nothing     -- works for strings and int
    assert lookup('request__url', 'http://example.com', entry1)
    assert not lookup('request_url', 'http://example.org', entry1)
    assert lookup('response__status', 404, entry1)
    assert not lookup('response__status', 404, entry2)
    assert lookup('response_unknown', None, entry1)


def test_filter_items():
    entries = entries_fixtures

    # when no lookup kwargs passed, all entries are returned
    assert_list_equal(fe(entries), entries)

    # simple 1st level lookups
    assert_list_equal(fe(entries, request__url='http://example.com'), entries[0:1])
    assert_list_equal(fe(entries, response__status=200), entries[1:])
    assert len(fe(entries, response__status=405)) == 0

    # testing compund lookups
    assert len(fe(entries, Q(request__url__exact='http://example.org'))) == 1
    assert len(fe(entries,
                  Q(request__url__exact='http://example.org', response__status=200)
                  |
                  Q(request__url__endswith='.com', response__status=404))) == 2

    assert len(fe(entries,
                  ~Q(request__url__exact='http://example.org', response__status__gte=500)
                  |
                  Q(request__url__endswith='.com', response__status=404))) == 3

    assert len(fe(entries,
                  ~Q(request__url__exact='http://example.org', response__status__gte=500)
                  |
                  Q(request__url__endswith='.com', response__status=404),
                  response__status__exact=200)) == 2


def test_include_keys():
    entries = entries_fixtures
    assert_list_equal(ik(entries, ['request']),
                      [{'request': {'url': 'http://example.com', 'headers': [{'name': 'Connection', 'value': 'Keep-Alive'}]}},
                       {'request': {'url': 'http://example.org', 'headers': [{'name': 'Connection', 'value': 'Keep-Alive'}]}},
                       {'request': {'url': 'http://example.com/myphoto.jpg', 'headers': [{'name': 'Connection', 'value': 'Keep-Alive'}]}}])

    assert_list_equal(ik(entries, ['response__status']),
                      [{'response__status': 404},
                       {'response__status': 200},
                       {'response__status': 200}])

    # when an empty list is passed as fields
    assert_list_equal(ik(entries, []), [{},{},{}])

    # when a non-existent key is passed in fields
    assert_list_equal(ik(entries, ['response__status', 'cookies']),
                      [{'response__status': 404, 'cookies': None},
                       {'response__status': 200, 'cookies': None},
                       {'response__status': 200, 'cookies': None}])


def test_Collection_QuerySet():
    data = [{'framework': 'Django', 'language': 'Python', 'type': 'full-stack'},
            {'framework': 'Flask', 'language': 'Python', 'type': 'micro'},
            {'framework': 'Rails', 'language': 'Ruby', 'type': 'full-stack'},
            {'framework': 'Sinatra', 'language': 'Ruby', 'type': 'micro'},
            {'framework': 'Zend', 'language': 'PHP', 'type': 'full-stack'},
            {'framework': 'Slim', 'language': 'PHP', 'type': 'micro'}]
    c = Collection(data)
    r1 = c.filter(framework__startswith='S')
    assert isinstance(r1, QuerySet)
    assert len(list(r1)) == 2
    r2 = c.filter(Q(language__exact='Python') | Q(language__exact='Ruby'))
    assert len(list(r2)) == 4
    r3 = c.filter(language='PHP')
    assert_list_equal(list(r3.select('framework', 'type')),
                      [{'framework': 'Zend', 'type': 'full-stack'},
                       {'framework': 'Slim', 'type': 'micro'}])
    r4 = c.filter(Q(language__exact='Python') | Q(language__exact='Ruby'))
    assert_list_equal(list(r4.select('framework')),
                      [{'framework': 'Django'},
                       {'framework': 'Flask'},
                       {'framework': 'Rails'},
                       {'framework': 'Sinatra'}])
    # :todo: test with flatten=True
    r5 = c.filter(framework__startswith='S').select('framework', 'somekey')
    assert_list_equal(list(r5),
                      [{'framework': 'Sinatra', 'somekey': None},
                       {'framework': 'Slim', 'somekey': None}])


## nesdict tests

def test_dunderkey():
    assert dunderkey('a', 'b', 'c') == 'a__b__c'
    assert dunderkey('a') == 'a'
    assert dunderkey('name', 'school_name') == 'name__school_name'


def test_dunder_partition():
    assert dunder_partition('a__b') == ('a', 'b')
    assert dunder_partition('a__b__c') == ('a__b', 'c')
    assert dunder_partition('a') == ('a', None)


def test_dunder_init():
    assert dunder_init('a__b') == 'a'
    assert dunder_init('a__b__c') == 'a__b'
    assert dunder_init('a') == 'a'


def test_dunder_last():
    assert dunder_last('a__b') == 'b'
    assert dunder_last('a__b__c') == 'c'
    assert dunder_last('a') == None


def test_dunder_get():
    d = dict([('a', 'A'),
              ('p', {'q': 'Q'}),
              ('x', {'y': {'z': 'Z'}})])
    assert dunder_get(d, 'a') == 'A'
    assert dunder_get(d, 'p__q') == 'Q'
    assert dunder_get(d, 'x__y__z') == 'Z'


def test_undunder_keys():
    entry = {'request__url': 'http://example.com', 'request__headers': [{'name': 'Connection', 'value': 'Keep-Alive',}],
             'response__status': 404, 'response__headers': [{'name': 'Date', 'value': 'Thu, 13 Jun 2013 06:43:14 GMT'}]}
    assert_equal(undunder_keys(entry),
                 {'request': {'url': 'http://example.com', 'headers': [{'name': 'Connection', 'value': 'Keep-Alive',}]},
                  'response': {'status': 404, 'headers': [{'name': 'Date', 'value': 'Thu, 13 Jun 2013 06:43:14 GMT'}]}})


def test_dunder_truncate():
    entry = {'request__url': 'http://example.com', 'request__headers': [{'name': 'Connection', 'value': 'Keep-Alive',}],
             'response__status': 404, 'response__headers': [{'name': 'Date', 'value': 'Thu, 13 Jun 2013 06:43:14 GMT'}]}
    assert_equal(dunder_truncate(entry),
                 {'url': 'http://example.com',
                  'request__headers': [{'name': 'Connection', 'value': 'Keep-Alive',}],
                  'status': 404,
                  'response__headers': [{'name': 'Date', 'value': 'Thu, 13 Jun 2013 06:43:14 GMT'}]})

