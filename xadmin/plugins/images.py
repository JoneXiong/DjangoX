import urlparse

from django.db import models
from django import forms
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.conf import settings
from xadmin.sites import site
from xadmin.views import BasePlugin, ModelFormAdminView, DetailAdminView, ListAdminView


def get_gallery_modal():
    return """
        <!-- modal-gallery is the modal dialog used for the image gallery -->
        <div id="modal-gallery" class="modal modal-gallery fade" tabindex="-1">
          <div class="modal-dialog">
            <div class="modal-content">
              <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                <h4 class="modal-title"></h4>
              </div>
              <div class="modal-body"><div class="modal-image"><h1 class="loader"><i class="fa-spinner fa-spin fa fa-large loader"></i></h1></div></div>
              <div class="modal-footer">
                  <a class="btn btn-info modal-prev"><i class="fa fa-arrow-left"></i> <span>%s</span></a>
                  <a class="btn btn-primary modal-next"><span>%s</span> <i class="fa fa-arrow-right"></i></a>
                  <a class="btn btn-success modal-play modal-slideshow" data-slideshow="5000"><i class="fa fa-play"></i> <span>%s</span></a>
                  <a class="btn btn-default modal-download" target="_blank"><i class="fa fa-download"></i> <span>%s</span></a>
              </div>
            </div><!-- /.modal-content -->
          </div><!-- /.modal-dialog -->
        </div>
    """ % (_('Previous'), _('Next'), _('Slideshow'), _('Download'))


class AdminImageField(forms.ImageField):

    def widget_attrs(self, widget):
        return {'label': self.label}


class AdminImageWidget(forms.FileInput):
    """
    A ImageField Widget that shows its current value if it has one.
    """
    def __init__(self, attrs={}):
        super(AdminImageWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        output = []
        if value:
            db_value = str(value)
            if db_value.startswith('/'):
                file_path = urlparse.urljoin(settings.REMOTE_MEDIA_URL, db_value)
            elif hasattr(value, "url"):
                file_path = value.url
            else:
                file_path = ''
            label = self.attrs.get('label', name)
            output.append('<a href="%s" target="_blank" title="%s" data-gallery="gallery"><img src="%s" class="field_img"/></a><br/>%s ' %
                         (file_path, label, file_path, _('Change:')))
        output.append(super(AdminImageWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))


class ModelDetailPlugin(BasePlugin):

    def __init__(self, admin_view):
        super(ModelDetailPlugin, self).__init__(admin_view)
        self.include_image = False

    def get_field_attrs(self, attrs, db_field, **kwargs):
        if isinstance(db_field, models.ImageField):
            attrs['widget'] = AdminImageWidget
            attrs['form_class'] = AdminImageField
            self.include_image = True
        return attrs

    def get_field_result(self, result, field_name):
        if isinstance(result.field, models.ImageField):
            if result.value:
                img = getattr(result.obj, field_name)
                db_value = str(img)
                if db_value.startswith('/'):
                    file_path = urlparse.urljoin(settings.REMOTE_MEDIA_URL, db_value)
                else:
                    file_path = img.url
                result.text = mark_safe('<a href="%s" target="_blank" title="%s" data-gallery="gallery"><img src="%s" class="field_img"/></a>' % (file_path, result.label, file_path))
                self.include_image = True
        return result

    # Media
    def get_media(self, media):
        if self.include_image:
            media = media + self.vendor('image-gallery.js',
                                        'image-gallery.css')
        return media

    def block_before_fieldsets(self, context, node):
        if self.include_image:
            return '<div id="gallery" data-toggle="modal-gallery" data-target="#modal-gallery">'

    def block_after_fieldsets(self, context, node):
        if self.include_image:
            return "</div>"

    def block_extrabody(self, context, node):
        if self.include_image:
            return get_gallery_modal()


class ModelListPlugin(BasePlugin):

    list_gallery = False

    def init_request(self, *args, **kwargs):
        return bool(self.list_gallery)
    
    def result_item(self, item, obj, field_name, row):
        opts = obj._meta
        try:
            f = opts.get_field(field_name)
        except models.FieldDoesNotExist:
            f = None
        if f:
            if isinstance(f, models.ImageField):
                img = getattr(obj, field_name)
                if img:
                    db_value = str(img)
                    if db_value.startswith('/'):
                        file_path = urlparse.urljoin(settings.REMOTE_MEDIA_URL, db_value)
                    else:
                        file_path = img.url
                    if type(self.list_gallery)==str:
                        file_path = '%s%s'%(file_path,self.list_gallery)
                    item.text = mark_safe('<a href="%s" target="_blank" data-gallery="gallery"><img src="%s" class="field_img"/></a>' % (file_path, file_path))
        return item

    # Media
    def get_media(self, media):
        return media + self.vendor('image-gallery.js', 'image-gallery.css')

    def block_results_top(self, context, node):
        return '<div id="gallery" data-toggle="modal-gallery" data-target="#modal-gallery">'

    def block_results_bottom(self, context, node):
        return "</div>"

    def block_extrabody(self, context, node):
        return get_gallery_modal()


site.register_plugin(ModelDetailPlugin, DetailAdminView)
site.register_plugin(ModelDetailPlugin, ModelFormAdminView)
site.register_plugin(ModelListPlugin, ListAdminView)
