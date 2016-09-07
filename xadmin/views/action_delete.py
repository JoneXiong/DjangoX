# coding=utf-8

from django.core.exceptions import PermissionDenied
from django.db import router
from django.utils.encoding import force_unicode
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
from django.utils.encoding import force_text
from django.contrib.contenttypes.models import ContentType

from base import filter_hook
from xadmin.views.action import Action
from xadmin.util import get_deleted_objects, model_ngettext
from xadmin.defs import ACTION_CHECKBOX_NAME

class DeleteSelectedAction(Action):

    action_name = "delete_selected"
    verbose_name = _(u'Delete selected %(verbose_name_plural)s')

    delete_confirmation_template = None
    delete_selected_confirmation_template = None

    model_perm = 'delete'
    icon = 'fa fa-times'
    
    def do_deletes(self, queryset):
        if self.log:
            for obj in queryset:
                self.log_deletion(self.request, obj)
        queryset.delete()

    @filter_hook
    def delete_models(self, queryset):
        u'''orm删除对象'''
        n = queryset.count()
        if n:
            self.do_deletes(queryset)
            self.message_user(_("Successfully deleted %(count)d %(items)s.") % {"count": n, "items": model_ngettext(self.opts, n) }, 'success')

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
        
    def log_deletion(self, request, object):
        """
        删除对象日志
        """
        from django.contrib.admin.models import LogEntry, DELETION
        LogEntry.objects.log_action(
            user_id         = request.user.pk,
            content_type_id = ContentType.objects.get_for_model(self.model).pk,
            object_id       = object.pk,
            object_repr     = force_text(object),
            action_flag     = DELETION
        )