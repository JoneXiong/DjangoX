# coding=utf-8
"""
为列表页面提供数据选择功能, 选择数据Action处理.
"""
from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _, ungettext
from django.utils.text import capfirst

from xadmin.sites import site
from xadmin.util import model_format_dict
from xadmin.views import BasePlugin, ListAdminView
from xadmin.views.page import GridPage
from xadmin.defs import ACTION_CHECKBOX_NAME
from xadmin.views.action import BaseActionView
from xadmin.views.action_delete import DeleteSelectedAction
from xadmin.views.grid import BaseGrid
from xadmin.views import UpdateAdminView
from xadmin.core.structs import SortedDict

checkbox_form_field = forms.CheckboxInput({'class': 'action-select'}, lambda value: False)

#  定义一个显示列 用于展示选择框
def action_checkbox(obj):
    if type(obj)==dict:
        _pk = obj['_pk']
    else:
        _pk = obj.pk
    return checkbox_form_field.render(ACTION_CHECKBOX_NAME, force_unicode(_pk))
action_checkbox.short_description = mark_safe(
    '<input type="checkbox" id="action-toggle" />')
action_checkbox.allow_tags = True
action_checkbox.allow_export = False
action_checkbox.is_column = False


class ActionPlugin(BasePlugin):

    # 配置项目
    actions = []
    can_select_all = False
    can_select = True
    can_delete_multi = True
    

    def init_request(self, *args, **kwargs):
        self.actions = self._get_actions()
        return self.can_select

    def get_list_display(self, list_display):
        list_display.insert(0, 'action_checkbox')
        self.admin_view.action_checkbox = action_checkbox
        return list_display

    def get_list_display_links(self, list_display_links):
        if len(list_display_links) == 1 and list_display_links[0] == 'action_checkbox':
            return list(self.admin_view.list_display[1:2])
        return list_display_links
    
    def _get_action_choices(self):
        choices = []
        if type(self.actions)==SortedDict:
            for ac, name, verbose_name, icon in self.actions.itervalues():
                if self.opts:
                    choice = (name, verbose_name % model_format_dict(self.opts), icon)
                else:
                    choice = (name, verbose_name, icon)
                choices.append(choice)
        else:
            for ac in self.actions:
                ac_url = ac.get_page_url()
                choices.append( (ac_url+'?', ac.verbose_name, ac.icon) )
        return choices

    def get_context(self, context):
        if self.admin_view.result_count:
            av = self.admin_view
            selection_note_all = ungettext('%(total_count)s selected', 'All %(total_count)s selected', av.result_count)
            m_action_choices = self._get_action_choices()
            new_context = {
                'selection_note': _('0 of %(cnt)s selected') % {'cnt': len(av.result_list)},
                'selection_note_all': selection_note_all % {'total_count': av.result_count},
                'action_choices': m_action_choices[:5],
                'action_choices_more': len(m_action_choices)>5 and m_action_choices[5:] or [],
            }
            context.update(new_context)
        return context

    def post_response(self, response, *args, **kwargs):
        request = self.admin_view.request
        av = self.admin_view

        # Actions with no confirmation
        if 'action' in request.POST:
            action = request.POST['action']

            if action not in self.actions or isinstance(av, GridPage):
                msg = '非法操作'
                av.message_user(msg)
            else:
                ac, name, description, icon = self.actions[action]
                # 是否为选择所有
                select_across = request.POST.get('select_across', False) == '1'
                selected = request.POST.getlist(ACTION_CHECKBOX_NAME)

                if not selected and not select_across:
                    msg = '请先选择'
                    av.message_user(msg)
                else:
                    queryset = av.list_queryset._clone()
                    if not select_across:
                        queryset = av.list_queryset.filter(pk__in=selected)
                    
                    ret = self._response_action(ac, queryset)
                    if isinstance(ret, basestring):
                        self.message_user(ret,'error')
                    if isinstance(ret, HttpResponse):
                        return ret
                    else:
                        return HttpResponseRedirect(self.action_view.get_redirect_url())
        return response

    def _response_action(self, ac, queryset):
        if isinstance(ac, type) and issubclass(ac, BaseActionView):
            action_view = self.get_model_view(ac, self.admin_view.model)
            self.action_view = action_view
            action_view.init_action(self.admin_view)
            return action_view.do_action(queryset)
        else:
            return ac(self.admin_view, self.request, queryset)

    def _get_actions(self):
        u'''获取所有action'''
        if not self.admin_view.opts:
            actions = self.actions or self.admin_view.form_actions
            return [ ac for ac in actions if not ac.perm  or ( ac.perm and self.user.has_perm('auth.'+ac.perm) ) ]
        
        if self.actions is None:
            return SortedDict()
        if self.model and self.admin_view.grid and self.can_delete_multi:
            actions = [self._get_action(action) for action in [DeleteSelectedAction] ]
        else:
            actions = []

        for klass in self.admin_view.__class__.mro()[::-1]:
            class_actions = getattr(klass, 'actions', [])
            if not class_actions:
                continue
            actions.extend(
                [self._get_action(action) for action in class_actions])

        actions = filter(None, actions)
        actions = SortedDict([
            (name, (ac, name, desc, icon))
            for ac, name, desc, icon in actions
        ])

        return actions

    def _get_action(self, action):
        u'''获取指定action的信息'''
        if isinstance(action, type) and issubclass(action, BaseActionView):
            if not action.has_perm(self.admin_view):
                return None
            return (
                    action, 
                    getattr(action, 'action_name') or 'act_%s'%action.__name__, 
                    getattr(action, 'verbose_name') or action.__name__, 
                    getattr(action, 'icon')
                    )
        # 对函数型action的支持
        elif callable(action):
            func = action
            action = action.__name__
        elif hasattr(self.admin_view.__class__, action):
            func = getattr(self.admin_view.__class__, action)
        else:
            return None
        if hasattr(func, 'short_description'):
            description = func.short_description
        else:
            description = action
        return func, action, description, getattr(func, 'icon', 'tasks')

    def result_header(self, item, field_name, row):
        if item.attr and field_name == 'action_checkbox':
            item.classes.append("action-checkbox-column")
        return item

    def result_item(self, item, obj, field_name, row):
        if item.field is None and field_name == u'action_checkbox':
            item.classes.append("action-checkbox")
        return item

    def get_media(self, media):
        if self.admin_view.result_count:
            media = media + self.vendor('xadmin.plugin.actions.js', 'xadmin.plugins.css')
        return media

    def block_results_bottom(self, context, nodes):
        if self.admin_view.result_count:
            _tpl = 'xadmin/blocks/grid.results_bottom.actions.html' if self.admin_view.grid else 'xadmin/blocks/form.results_bottom.actions.html'
            nodes.append(loader.render_to_string(_tpl, context_instance=context))


site.register_plugin(ActionPlugin, ListAdminView)
site.register_plugin(ActionPlugin, GridPage)
site.register_plugin(ActionPlugin, UpdateAdminView)