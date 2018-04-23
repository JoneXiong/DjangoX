# coding=utf-8

import os
import json

from django.core.management.base import CommandError, BaseCommand
from django.contrib.auth.models import ContentType, Permission, Group

from xadmin.models import add_view_permissions
from xadmin.initialize import autodiscover

autodiscover()
from xadmin import site


def get_page_perm():
    '''
    获取所有page页面的权限代码
    :return:
    '''
    return [(page.perm, page.verbose_name) for page in site._registry_pages if page.perm]


def get_action_perm():
    '''
    获取所有的action权限代码
    :return:
    '''
    all_actions = [v.actions for k, v in site._registry.iteritems() if hasattr(v, 'actions')]
    actions = []
    for each_atcs in all_actions:
        if each_atcs:
            actions.extend(each_atcs)

    return [(each_atc.perm, each_atc.verbose_name) for each_atc in actions if each_atc.perm]

def get_or_create_perm(name, codename, content_type):
    '''
    创建不存在的权限
    :param name:
    :param codename:
    :param content_type:
    :return:
    '''
    return Permission.objects.get_or_create(name=name, codename=codename, content_type=content_type)

def auto_create_or_update_perm():
    '''
    创建所有page和action的权限
    :return:
    '''
    common_content_type = ContentType.objects.filter(app_label='auth', model='permission')[0]
    all_perm = get_page_perm() + get_action_perm()
    for perm_code, perm_name in all_perm:
        try:
            _perm,_is_create =  get_or_create_perm(perm_name, perm_code, common_content_type)
            if _is_create:
                print('Created perm: %s'%_perm)
        except:
            import traceback;traceback.print_exc()
            print('Error to create: %s %s'%(perm_code, perm_name))

	add_view_permissions(1)

class Command(BaseCommand):

    help = (u"Sync all page、action and model view permissions.")

    def handle(self, *args, **options):
        auto_create_or_update_perm()
        print('Done.')

