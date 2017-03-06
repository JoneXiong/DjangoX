import django
from django.conf.urls import include, url
from django.conf import settings


from django.views.generic import TemplateView
from .views.register import RegisterView, LoginView,ActiveUserView, ForgetView, ResetPasswordView, ModifyPasswordView

urlpatterns = [
    url(r'^captcha/', include('captcha.urls')),
    url(r'^register/', RegisterView.as_view(), name='register'),
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^active/(?P<active_code>.*)/$', ActiveUserView.as_view(), name='user_active'),
    url(r'^forget/$', ForgetView.as_view(), name="forget_password"),
    url(r'^reset/(?P<active_code>.*)/$', ResetPasswordView.as_view(), name='reset_password'),
    url(r'^modify_password/$', ModifyPasswordView.as_view(), name='modify_password'),
    url(r'^$', TemplateView.as_view(template_name="account/auth/index.html"), name='index'),
]
