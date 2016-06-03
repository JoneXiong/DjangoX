# coding=utf-8

import xadmin
from xadmin.views.form import FormView

from form import TestForm

class TestFormView(FormView):
    form = TestForm
    title = u'测试表单视图'

    def save_forms(self):
        data = self.form_obj.cleaned_data
        print '>>>',data

    def post_response(self):
        pass
        #失败示例
        #self.message_user('Le code du dossier ne dois contenir que des chiffres', 'error')
        #return self.get_response()

        #成功示例
        if not self.request.is_ajax() or self.request.GET.get('_ajax'):
            self.message_user(u'账户明细导入成功', 'success')
            return self.get_redirect_url()
        else:
            #ajax提交成功示例
            self.message_user(u'账户明细导入成功', 'success')
            return self.render_response({'result': 'success',})
            
        #ajax提交失败示例
        from xadmin.plugins.ajax import JsonErrorDict
        form = self.form_obj
        result = {}
        if form.is_valid():
            result['result'] = 'success'
        else:
            result['result'] = 'error'
            result['errors'] = JsonErrorDict(form.errors, form).as_json()
        return self.render_response(result)

    
    def get_initial_data(self):
        # 初始化数据
        return {'title':'joe test'}
    
xadmin.site.register_view(r'^test_form$', TestFormView, name='TestFormView')