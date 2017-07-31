# coding=utf-8

import xadmin
from xadmin.layout import Fieldset, Field

from app import models

class ArticleAdmin(object):
    list_display = ('title', 'categories', 'date')
    list_display_links = ('title',)

    search_fields = ('title', 'content')
    list_editable = ('date',)
    list_filter = ('categories', 'date')

    form_layout = (
        Fieldset('基本信息',
            'title', 'date'
        ),
        Fieldset('文章内容',
            Field('content')#, template="xcms/content_field.html")
        ),
    )
    #style_fields = {'content': 'wysi_ck', 'categories':'m2m_tree'}
xadmin.site.register(models.Article, ArticleAdmin)

class CategoryAdmin(object):
    list_display = ('name', 'parent')
    list_display_links = ('id', 'name',)

    search_fields = ('name', )
    list_editable = ('name', )
    list_filter = ('parent', )

xadmin.site.register(models.Category, CategoryAdmin)
