from django.db import models

from xadmin.sites import site
from xadmin.views import BasePlugin, ModelFormAdminView
from xadmin import widgets

class RelateFieldPlugin(BasePlugin):

    def get_field_style(self, attrs, db_field, style, **kwargs):
        if (style == 'fk_ajax' or style == 'fk-ajax') and isinstance(db_field, models.ForeignKey):
            #if (db_field.rel.to in self.admin_view.admin_site._registry) and self.has_model_perm(db_field.rel.to, 'view'):
            db = kwargs.get('using')
            return dict(attrs or {}, widget=widgets.ForeignKeySearchWidget(db_field.rel, self.admin_view, using=db))
        if (style == 'fk_raw' or style == 'fk-raw') and isinstance(db_field, models.ForeignKey):
            #if (db_field.rel.to in self.admin_view.admin_site._registry) and self.has_model_perm(db_field.rel.to, 'view'):
            db = kwargs.get('using')
            return dict(attrs or {}, widget=widgets.ForeignKeyRawIdWidget(db_field.rel, self.admin_view, using=db))
        if style == 'fk_select' and isinstance(db_field, models.ForeignKey):
            db = kwargs.get('using')
            return dict(attrs or {}, widget=widgets.SelectWidget)
        return attrs

site.register_plugin(RelateFieldPlugin, ModelFormAdminView)
