# coding=utf-8

from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from django.utils.encoding import force_unicode

from xadmin import dutils

NON_FIELD_ERRORS = '__all__'


class JsonErrorDict(dutils.ErrorDict):

    def __init__(self, errors, form):
        super(JsonErrorDict, self).__init__(errors)
        self.form = form

    def as_json(self):
        if not self:
            return u''
        return [{'id': self.form[k].auto_id if k != NON_FIELD_ERRORS else NON_FIELD_ERRORS, 'name': k, 'errors': v} for k, v in self.items()]


class FakeMethodField(object):
    u"""
    方法型字段的包装类
    """
    def __init__(self, name, verbose_name):
        self.name = name
        self.verbose_name = verbose_name
        self.primary_key = False


class ResultRow(dict):
    u"""
    数据行
    """
    def __init__(self):
        self.cells = []
        
    def add_cell(self,name, text):
        item = ResultItem(name, self)
        item.text = text
        self.cells.append(item)


class ResultItem(object):
    u"""
    数据单元格
    """
    def __init__(self, field_name, row):
        self.classes = []
        self.text = '&nbsp;'
        self.wraps = []
        self.tag = 'td'
        self.tag_attrs = []
        self.allow_tags = False
        self.btns = []
        self.menus = []
        self.is_display_link = False
        self.row = row
        self.field_name = field_name
        self.field = None
        self.attr = None
        self.value = None

    @property
    def label(self):
        text = mark_safe(
            self.text) if self.allow_tags else conditional_escape(self.text)
        if force_unicode(text) == '':
            text = mark_safe('&nbsp;')
        for wrap in self.wraps:
            text = mark_safe(wrap % text)
        return text

    @property
    def tagattrs(self):
        return mark_safe(
            '%s%s' % ((self.tag_attrs and ' '.join(self.tag_attrs) or ''),
            (self.classes and (' class="%s"' % ' '.join(self.classes)) or '')))


class ResultHeader(ResultItem):
    u"""
    表头单元格
    """
    def __init__(self, field_name, row):
        super(ResultHeader, self).__init__(field_name, row)
        self.tag = 'th'
        self.tag_attrs = ['scope="col"']
        self.sortable = False
        self.allow_tags = True
        self.sorted = False
        self.ascending = None
        self.sort_priority = None
        self.url_primary = None
        self.url_remove = None
        self.url_toggle = None
