import django
from django.conf.urls import include, url#,patterns
from django.conf import settings
from django.conf.urls.static import static

# Uncomment the next two lines to enable the admin:
import xadmin
xadmin.ROOT_PATH_NAME = 'xadmin'
settings.XADMIN_EXCLUDE_PLUGINS = ['bookmark']

xadmin.autodiscover()


from django.contrib import admin
admin.autodiscover()


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^xadmin/', include(xadmin.site.urls)),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
