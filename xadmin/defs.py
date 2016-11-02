# -*- coding: utf-8 -*-

from django.utils.translation import ugettext as _

# 数据表格中的值为空时显示的值
EMPTY_CHANGELIST_VALUE = 'Null'

FILTER_PREFIX = '_p_'

SEARCH_VAR = '_q_'

DEFAULT_MODEL_ICON = 'fa fa-circle-o'

DEFAULT_SITE_TITLE = u'Django Xadmin'

DEFAULT_SITE_FOOTER = u'my-company.inc 2013'

BUILDIN_STYLES = {
    'default': 'xadmin/includes/sitemenu_default.html',
    'accordion': 'xadmin/includes/sitemenu_accordion.html',
    'inspinia': 'xadmin/includes/sitemenu_inspinia.html'
}

TO_FIELD_VAR = 't'
SHOW_FIELD_VAR = 's'

ACTION_CHECKBOX_NAME = '_selected_action'

# list 页用到的
ALL_VAR = 'all'

ORDER_VAR = 'o'

PAGE_VAR = 'p'

COL_LIST_VAR = '_cols'

ERROR_FLAG = 'e'

DOT = '.'
