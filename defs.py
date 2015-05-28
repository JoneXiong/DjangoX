# -*- coding: utf-8 -*-

from django.utils.translation import ugettext as _

# 数据表格中的值为空时显示的值
EMPTY_CHANGELIST_VALUE = _('Null')

FILTER_PREFIX = '_p_'

SEARCH_VAR = '_q_'

DEFAULT_MODEL_ICON = 'fa fa-circle-o'

DEFAULT_SITE_TITLE = u'Django Xadmin'

DEFAULT_SITE_FOOTER = u'my-company.inc 2013'

BUILDIN_STYLES = {
    'default': 'xadmin/includes/sitemenu_default.html',
    'accordion': 'xadmin/includes/sitemenu_accordion.html',
}