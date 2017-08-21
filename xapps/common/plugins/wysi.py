#coding:utf-8
import xadmin
from django.db.models import TextField
from xadmin import widgets
from xadmin.views import BasePlugin, ModelFormAdminView, DetailAdminView


class WYSIHtml5Plugin(BasePlugin):

    def init_request(self, *args, **kwargs):
        self.include_html5 = False
        self.include_tinymce = False
        self.include_ckediter = False
        if hasattr(self.admin_view, 'style_fields'):
            styles = self.admin_view.style_fields.values()
            return ('wysi_html5' in styles or 'wysi_tinymce' in styles or 'wysi_ck' in styles)
        else:
            return False

    def get_field_style(self, attrs, db_field, style, **kwargs):
        if isinstance(db_field, TextField):
            if style == 'wysi_html5':
                self.include_html5 = True
                return {'widget': widgets.AdminTextareaWidget(attrs={'class': 'textarea-field wysi_html5'})}
            if style == 'wysi_tinymce':
                self.include_tinymce = True
                return {'widget': widgets.AdminTextareaWidget(attrs={'class': 'textarea-field wysi_tinymce'})}
            if style == 'wysi_ck':
                self.include_ckediter = True
                return {'widget': widgets.AdminTextareaWidget(attrs={'class': 'textarea-field wysi_ck ckeditor'})}
        return attrs

    def get_field_result(self, result, field_name):
        if self.admin_view.style_fields.get(field_name) in ('wysi_html5', 'wysi_tinymce', 'wysi_ck'):
            result.allow_tags = True
        return result

    # Media
    def get_media(self, media):
        if self.include_html5:
            media.add_js([self.static('common/js/wysihtml5-0.3.0.min.js'),
                self.static('common/js/bootstrap-wysihtml5.js'),
                self.static('common/js/locales/bootstrap-wysihtml5.zh-CN.js'),
                self.static('common/js/form_wysi.js')])
            media.add_css({'screen': [self.static('common/css/wysiwyg-color.css'), self.static('common/css/bootstrap-wysihtml5.css')]})
        if self.include_tinymce:
            media.add_js([
                self.static('common/tiny_mce/jquery.tinymce.js'),
                self.static('common/js/form_wysi.js')])
        if self.include_ckediter:
            media.add_js([self.static('common/ckeditor/ckeditor.js'),])
        return media

xadmin.site.register_plugin(WYSIHtml5Plugin, DetailAdminView)
xadmin.site.register_plugin(WYSIHtml5Plugin, ModelFormAdminView)
