# coding=utf-8

from base import filter_hook, ModelAdminView

class BaseActionView(ModelAdminView):
    action_name = None
    #description = None
    verbose_name = None
    icon = 'fa fa-tasks'

    model_perm = None#'change'
    perm = None

    @classmethod
    def has_perm(cls, list_view):
        if cls.model_perm:
            perm_code = cls.model_perm
        else:
            perm_code = cls.perm or cls.__name__
            perm_code= 'auth.'+perm_code
        return list_view.has_permission(perm_code)

    def init_action(self, list_view):
        self.list_view = list_view
        self.admin_site = list_view.admin_site

    @filter_hook
    def do_action(self, queryset):
        pass
    
Action = BaseActionView