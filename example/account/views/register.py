# coding=utf-8

from django import forms
from django.views.generic import View
from captcha.fields import CaptchaField
from django.shortcuts import render
from django.contrib.auth import authenticate, login as my_login
from django.http import HttpResponseRedirect


from django.contrib.auth.hashers import make_password
from account.models import EmailVerifyRecord
from xadmin.util import User as UserProfile
from xadmin import site

auth_tpl_path = 'account/auth/'


def generate_random_string(random_length=8):
    from random import Random

    string = ''
    chars = 'abdcefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(random_length):
        string += chars[random.randint(0, length)]
    return string

def send_register_email(email, send_type="register"):
    from xadmin.models import EmailVerifyRecord
    from django.core.mail import send_mail

    EMAIL_FROM = 'jianhongxiong@kingthy.com'
    HOST = '192.168.1.153:8080'

    email_record = EmailVerifyRecord()
    code = generate_random_string(random_length=16)
    email_record.code = code
    email_record.email = email
    email_record.send_type = send_type
    email_record.save()
    # send email to register
    if send_type == 'register':
        email_title = 'DjangoX注册激活链接'
        email_body = '请点击下面的链接激活你的帐号：{0}{1}{2}'.format('http://'+HOST+'/active/', code, '/')
        send_status = send_mail(email_title, email_body, EMAIL_FROM, [email])
        if send_status:
            pass
    # send email to reset password
    elif send_type == 'forget':
        email_title = 'DjangoX密码重置链接'
        email_body = '请点击下面的链接重置你的密码：{0}{1}{2}'.format('http://'+HOST+'/reset/', code, '/')
        send_status = send_mail(email_title, email_body, EMAIL_FROM, [email])
        if send_status:
            pass



class ActiveUserView(View):
    def get(self, request, active_code):
        all_records = EmailVerifyRecord.objects.filter(code=active_code)
        if all_records:
            for record in all_records:
                email = record.email
                user = UserProfile.objects.get(email=email)
                user.is_active = True
                user.save()
        else:
            return render(request, auth_tpl_path+'active_fail.html')
        return render(request, auth_tpl_path+'login.html')

class RegisterForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True, min_length=6)
    captcha = CaptchaField(error_messages={"invalid": u"验证码错误"})


class RegisterView(View):
    def get(self, request):
        register_form = RegisterForm()
        data = {
            'register_form': register_form,
            'site': site,
        }
        return render(request, auth_tpl_path+"register.html", data)

    def post(self, request):
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            username = request.POST.get('email', "")
            if UserProfile.objects.filter(email=username):
                data = {
                    'register_form': register_form,
                    'message': '邮箱已经被注册'
                }
                return render(request, auth_tpl_path+'register.html', data)
            password = request.POST.get('password', "")
            user_profile = UserProfile()
            user_profile.username = username
            user_profile.email = username
            user_profile.is_active = False
            user_profile.password = make_password(password)
            user_profile.save()
            send_register_email(username, 'register')
            return render(request, auth_tpl_path+'login.html')
        else:
            data = {
                'register_form': register_form,
                'site': site,
            }
            return render(request, auth_tpl_path+'register.html', data)

class LoginForm(forms.Form):
    username = forms.CharField(required=True, min_length=4)
    password = forms.CharField(required=True, min_length=4)
    captcha = CaptchaField(error_messages={"invalid": u"验证码错误"})

class LoginView(View):
    def get(self, request):
        login_form = LoginForm()
        data = {
            'login_form': login_form,
            'site': site,
        }
        return render(request, auth_tpl_path+'login.html', data)

    def post(self, request):
        login_form = LoginForm(request.POST)
        username = request.POST.get('username', "")
        password = request.POST.get('password', "")
        if login_form.is_valid():
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    my_login(request, user)
                    return HttpResponseRedirect('/')
                else:
                    data = {
                        'message': '用户未激活',
                        'login_form': login_form
                    }
                    return render(request, auth_tpl_path+'login.html', data)
            else:
                data = {
                    'message': '用户名或者密码出错',
                    'login_form': login_form,
                    'username': username,
                    'password': password
                }
                return render(request, auth_tpl_path+'login.html', data)
        else:
            data = {
                'message': '未通过用户名或密码格式验证',
                'login_form': login_form,
                'username': username,
                'password': password,
                'site': site,
            }
            return render(request, auth_tpl_path+'login.html', data)


class ForgetForm(forms.Form):
    email = forms.EmailField(required=True)
    captcha = CaptchaField(error_messages={"invalid": u"验证码错误"})


class ModifyPasswordForm(forms.Form):
    password1 = forms.CharField(required=True, min_length=6)
    password2 = forms.CharField(required=True, min_length=6)


class ForgetView(View):
    def get(self, request):
        forget_form = ForgetForm()
        data = {
            'forget_form': forget_form,
            'site': site,
        }
        return render(request, auth_tpl_path+'forgetpwd.html', data)

    def post(self, request):
        forget_form = ForgetForm(request.POST)
        email = request.POST.get('email', '')
        if forget_form.is_valid():
            send_register_email(email, send_type='forget')
            return render(request, auth_tpl_path+'sendemail_success.html')
        else:
            data = {
                'forget_form': forget_form,
                'email': email,
                'site': site,
            }
            return render(request, auth_tpl_path+'forgetpwd.html', data)


class ResetPasswordView(View):
    def get(self, request, active_code):
        all_records = EmailVerifyRecord.objects.filter(code=active_code)
        if all_records:
            for record in all_records:
                email = record.email
                data = {
                    'email': email
                }
                return render(request, auth_tpl_path+'password_reset.html', data)
        else:
            return render(request, auth_tpl_path+'active_fail.html')


class ModifyPasswordView(View):
    def post(self, request):
        password_form = ModifyPasswordForm(request.POST)
        if password_form.is_valid():
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')
            email = request.POST.get('email', '')
            if password1 != password2:
                data = {
                    'email': email,
                    'message': '两次密码不一致'
                }
                return render(request, auth_tpl_path+'password_reset.html', data)
            else:
                user_profile = UserProfile.objects.get(email=email)
                user_profile.password = make_password(password1)
                user_profile.save()
                return render(request, auth_tpl_path+'login.html')
        else:
            data = {
                'message': '密码填写规则不符合要求'
            }
            return render(request, auth_tpl_path+'password_reset.html', data)
