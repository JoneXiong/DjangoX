# coding=utf-8
"""
在数据列表页面提供了数据选择功能, 选择后的数据可以经过 Action 做特殊的处理. 默认提供的 Action 为批量删除功能.
开发者可以设置 Model OptionClass 的 actions 属性, 该属性是一个列表, 包含您想启用的 Action 的类. 系统已经默认内置了删除数据的 Action,
"""
from django import forms
from django.core.exceptions import PermissionDenied
from django.db import router
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.template.response import TemplateResponse
from django.utils.datastructures import SortedDict
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _, ungettext
from django.utils.text import capfirst
from xadmin.sites import site
from xadmin.util import model_format_dict, get_deleted_objects, model_ngettext
from xadmin.views import BaseAdminPlugin, ListAdminView
from xadmin.views.base import filter_hook
from xadmin.views.page import GridPage
from xadmin.defs import ACTION_CHECKBOX_NAME
from xadmin.views.action import BaseActionView

checkbox = forms.CheckboxInput({'class': 'action-select'}, lambda value: False)

#  定义一个显示列 用于展示选择框
def action_checkbox(obj):
    return checkbox.render(ACTION_CHECKBOX_NAME, force_unicode(obj.pk))
action_checkbox.short_description = mark_safe(
    '<input type="checkbox" id="action-toggle" />')
action_checkbox.allow_tags = True
action_checkbox.allow_export = False
action_checkbox.is_column = False


class DeleteSelectedAction(BaseActionView):

    action_name = "delete_selected"
    verbose_name = _(u'Delete selected %(verbose_name_plural)s')

    delete_confirmation_template = None
    delete_selected_confirmation_template = None

    model_perm = 'delete'
    icon = 'fa fa-times'

    @filter_hook
    def delete_models(self, queryset):
        u'''orm删除对象'''
        n = queryset.count()
        if n:
            queryset.delete()
            self.message_user(_("Successfully deleted %(count)d %(items)s.") % {
                "count": n, "items": model_ngettext(self.opts, n)
            }, 'success')

    @filter_hook
    def do_action(self, queryset):
        # 检查是否有删除权限
        if not self.has_delete_permission():
            raise PermissionDenied

        using = router.db_for_write(self.model)

        # Populate deletable_objects, a data structure of all related objects that
        # will also be deleted.
        deletable_objects, perms_needed, protected = get_deleted_objects(
            queryset, self.opts, self.user, self.admin_site, using)

        # The user has already confirmed the deletion.
        # Do the deletion and return a None to display the change list view again.
        if self.request.POST.get('post'):
            if perms_needed:
                raise PermissionDenied
            self.delete_models(queryset)
            # Return None to display the change list page again.
            return None
        # GET请求 删除确认页面
        if len(queryset) == 1:
            objects_name = force_unicode(self.opts.verbose_name)
        else:
            objects_name = force_unicode(self.opts.verbose_name_plural)

        if perms_needed or protected:
            title = _("Cannot delete %(name)s") % {"name": objects_name}
        else:
            title = _("Are you sure?")

        context = self.get_context()
        context.update({
            "title": title,
            "objects_name": objects_name,
            "deletable_objects": [deletable_objects],
            'queryset': queryset,
            "perms_lacking": perms_needed,
            "protected": protected,
            "opts": self.opts,
            "app_label": self.app_label,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
        })

        return TemplateResponse(self.request, self.delete_selected_confirmation_template or
                                self.get_template_list('views/model_delete_selected_confirm.html'), context, current_app=self.admin_site.name)


class ActionPlugin(BaseAdminPlugin):

    # Actions
    actions = []
    actions_selection_counter = True
    global_actions = [DeleteSelectedAction]

    def init_request(self, *args, **kwargs):
        self.actions = self.get_actions()
        return bool(self.actions)

    def get_list_display(self, list_display):
        if self.actions:
            list_display.insert(0, 'action_checkbox')
            self.admin_view.action_checkbox = action_checkbox
        return list_display

    def get_list_display_links(self, list_display_links):
        if self.actions:
            if len(list_display_links) == 1 and list_display_links[0] == 'action_checkbox':
                return list(self.admin_view.list_display[1:2])
        return list_display_links

    def get_context(self, context):
        if self.actions and self.admin_view.result_count:
            av = self.admin_view
            selection_note_all = ungettext('%(total_count)s selected',
                                           'All %(total_count)s selected', av.result_count)
            m_action_choices = self.get_action_choices()
            new_context = {
                'selection_note': _('0 of %(cnt)s selected') % {'cnt': len(av.result_list)},
                'selection_note_all': selection_note_all % {'total_count': av.result_count},
                'action_choices': m_action_choices[:5],
                'action_choices_more': len(m_action_choices)>5 and m_action_choices[5:] or [],
                'actions_selection_counter': self.actions_selection_counter,
            }
            context.update(new_context)
        return context

    def post_response(self, response, *args, **kwargs):
        request = self.admin_view.request
        av = self.admin_view

        # Actions with no confirmation
        if self.actions and 'action' in request.POST:
            action = request.POST['action']

            if action not in self.actions:
                msg = _("Items must be selected in order to perform "
                        "actions on them. No items have been changed.")
                av.message_user(msg)
            else:
                ac, name, description, icon = self.actions[action]
                select_across = request.POST.get('select_across', False) == '1'
                selected = request.POST.getlist(ACTION_CHECKBOX_NAME)

                if not selected and not select_across:
                    # Reminder that something needs to be selected or nothing will happen
                    msg = _("Items must be selected in order to perform "
                            "actions on them. No items have been changed.")
                    av.message_user(msg)
                else:
                    queryset = av.list_queryset._clone()
                    if not select_across:
                        # Perform the action only on the selected objects
                        queryset = av.list_queryset.filter(pk__in=selected)
                    response = self.response_action(ac, queryset)
                    # Actions may return an HttpResponse, which will be used as the
                    # response from the POST. If not, we'll be a good little HTTP
                    # citizen and redirect back to the changelist page.
                    if isinstance(response, HttpResponse):
                        return response
                    else:
                        return HttpResponseRedirect(request.get_full_path())
        return response

    def response_action(self, ac, queryset):
        if isinstance(ac, type) and issubclass(ac, BaseActionView):
            action_view = self.get_model_view(ac, self.admin_view.model)
            action_view.init_action(self.admin_view)
            return action_view.do_action(queryset)
        else:
            return ac(self.admin_view, self.request, queryset)

    def get_actions(self):
        u'''获取所有action'''
        if self.actions is None:
            return SortedDict()
        if self.model:
            actions = [self.get_action(action) for action in self.global_actions]
        else:
            actions = []

        for klass in self.admin_view.__class__.mro()[::-1]:
            class_actions = getattr(klass, 'actions', [])
            if not class_actions:
                continue
            actions.extend(
                [self.get_action(action) for action in class_actions])

        # get_action might have returned None, so filter any of those out.
        actions = filter(None, actions)

        # Convert the actions into a SortedDict keyed by name.
        actions = SortedDict([
            (name, (ac, name, desc, icon))
            for ac, name, desc, icon in actions
        ])

        return actions

    def get_action_choices(self):
        """
        Return a list of choices for use in a form object.  Each choice is a
        tuple (name, verbose_name, icon).
        """
        choices = []
        for ac, name, verbose_name, icon in self.actions.itervalues():

#            class dg():
#                verbose_name = 'dg'
#                verbose_name_plural = 'dg_plural'
#            choice = (name, description % model_format_dict(dg), icon)
            if self.opts:
                choice = (name, verbose_name % model_format_dict(self.opts), icon)
            else:
                choice = (name, verbose_name, icon)
            choices.append(choice)
        return choices

    def get_action(self, action):
        u'''获取指定action的信息列表'''
        if isinstance(action, type) and issubclass(action, BaseActionView):
            if not action.has_perm(self.admin_view):
                return None
            return action, getattr(action, 'action_name') or 'act_%s'%action.__name__, getattr(action, 'verbose_name') or getattr(action, 'description'), getattr(action, 'icon')

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
            description = capfirst(action.replace('_', ' '))

        return func, action, description, getattr(func, 'icon', 'tasks')

    # View Methods
    def result_header(self, item, field_name, row):
        if item.attr and field_name == 'action_checkbox':
            item.classes.append("action-checkbox-column")
        return item

    def result_item(self, item, obj, field_name, row):
        if item.field is None and field_name == u'action_checkbox':
            item.classes.append("action-checkbox")
        return item

    # Media
    def get_media(self, media):
        if self.actions and self.admin_view.result_count:
            media = media + self.vendor('xadmin.plugin.actions.js', 'xadmin.plugins.css')
        return media

    # Block Views
    def block_results_bottom(self, context, nodes):
        if self.actions and self.admin_view.result_count:
            nodes.append(loader.render_to_string('xadmin/blocks/model_list.results_bottom.actions.html', context_instance=context))


site.register_plugin(ActionPlugin, ListAdminView)
# site.register_plugin(ActionPlugin, GridPage)
