# coding=utf-8

import os
import json

from django.conf import settings

from django.core.management.base import CommandError, BaseCommand
from django.contrib.auth.models import ContentType, Permission, Group

from xadmin.dutils import import_module


def gen_model_perm_code(model_name, model_perm):
    re_model_perm = []
    index_dict = {
        0: 'add',
        1: 'delete',
        2: 'change',
        3: 'view'
    }
    for index, each_perm in enumerate(model_perm):
        if int(each_perm):
            re_model_perm.append("{}_{}".format(index_dict.get(index), model_name))
    return re_model_perm


def sync_groups(group_dict):
    perm_need_add = []
    for group_name, group_perm in group_dict.iteritems():
        _group,_is_create = Group.objects.get_or_create(name=group_name)
        if _is_create:
            print 'Created group:',_group

        # 获取model的权限配置
        _group_model_perm = group_perm.get("model")
        for model_name, model_perm in _group_model_perm.iteritems():
            perm_need_add.extend([each_perm for each_perm in
                                  Permission.objects.filter(codename__in=gen_model_perm_code(model_name, model_perm))])

        # 获取action的权限配置
        _group_action_perm = group_perm.get("action")
        perm_need_add.extend([each_perm for each_perm in
                              Permission.objects.filter(codename__in=_group_action_perm)])

        # 获取page的权限配置
        _group_page_perm = group_perm.get("page")

        perm_need_add.extend([each_perm for each_perm in
                              Permission.objects.filter(codename__in=_group_page_perm)])

        _group.permissions.add(*perm_need_add)


class Command(BaseCommand):

    help = (u"Sync all page、action and model view permissions.")

    def handle(self, *args, **options):
        for app in settings.INSTALLED_APPS:
            try:
                perm_mod = import_module('%s.perm' % app)
                if hasattr(perm_mod,'perms'):
                    pass
                if hasattr(perm_mod,'groups'):
                    sync_groups(perm_mod.groups)
            except ImportError:
                pass
        print 'Done.'

