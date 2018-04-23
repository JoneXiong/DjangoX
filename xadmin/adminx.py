# coding=utf-8

from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType

import xadmin

from .models import UserSettings, SystemSettings


class UserSettingsAdmin(object):
    model_icon = 'fa fa-cog'
    hide_menu = False
    menu_group = 'other_group'
xadmin.site.register(UserSettings, UserSettingsAdmin)


class SystemSettingsAdmin(object):
    model_icon = 'fa fa-cog'
    hide_menu = False
    menu_group = 'other_group'
xadmin.site.register(SystemSettings, SystemSettingsAdmin)


class LogEntryAdmin(object):
    list_display = ['id', '__str__', 'object_id', 'content_type', 'user', 'action_time']
    list_filter = ['content_type']
    filter_default_list = ['content_type']
    filter_list_position = 'top'
    app_label = 'xadmin'
    menu_group = 'other_group'
xadmin.site.register(LogEntry, LogEntryAdmin)

class ContentTypeAdmin(object):
    app_label = 'xadmin'
    menu_group = 'other_group'
xadmin.site.register(ContentType, ContentTypeAdmin)
