# coding=utf-8
import re

from django import forms
from django.forms import Media
from ..util import vendor


class SelectRelation(forms.TextInput):
    '''
    使用示例：
    widget=SelectRelation(self, 'select1', {
                                     '1':  ForeignKeyPopupWidget(self, Host, 'id'),
                                     '2':  ForeignKeyPopupWidget(self, A, 'id'),
                                     '3':  ForeignKeyPopupWidget(self, B, 'id'),
                                     }
                            )

    '''
    
    def __init__(self, admin_view, link, map_dict, attrs=None, using=None,inline_ref=''):
        self.admin_view = admin_view
        self.link = link
        self.map_dict = map_dict
        self.inline_ref = inline_ref
        super(SelectRelation, self).__init__(attrs)
    
    def value_from_datadict(self, data, files, name):
        return data.get(name)
        link_val = data.get(self.link)
        cur_obj = self.map_dict[link_val]
        return cur_obj.value_from_datadict(data, files, name)
    
    def render(self, name, value, attrs=None,form=None):
        link_val = self.get_value(self.link, form)
        link_val = str(link_val)
        map_list = [( str(k),'%s-%s'%(self.link, id(v)) ) for k,v in self.map_dict.items()]
        _map = dict(map_list)
        if link_val and link_val!='None':
            cur_obj = self.map_dict.get(link_val,None)
        else:
            cur_obj=None
        _all = set(self.map_dict.values())
        output = []
        if self.inline_ref+'-__prefix__-' in name:
            _name = name.replace(self.inline_ref+'-__prefix__-','')
        else:
            _name = re.sub(self.inline_ref+'-\d+-','',name)
        _link = name.replace(_name,self.link)#'id_items-__prefix__-'+self.link
        for obj in _all:
            if obj==cur_obj:
                output.append( '''<div id="id_%s-%s">%s</div>'''%(_link, id(obj), obj.render(name, value, attrs) ) )
            else:
                output.append( '''<div id="id_%s-%s" style="display:none">%s</div>'''%(_link, id(obj), obj.render(name, None, attrs) ) )
        opt_list = ['<li key="%s">%s</li>'%(k,v) for k,v in _map.items()]
        output.append('''
                      <ul class="select-relation" name="%s" link="%s" style="display:none">%s</ul>
        '''%(_name,self.link,''.join(opt_list)))
        return ''.join(output)
        
    def get_value(self, key, form=None):
        '''
        得到关联字段的值
        '''
        if hasattr(self.admin_view,'form_obj'):
            self.form = self.admin_view.form_obj
        else:
            self.form = form
        if not self.form.is_bound:
            return self.form.initial.get(key,None)
        else:
            return self.form.data.get(key,None)
    
    @property
    def media(self):
        media = Media()
        _all = set(self.map_dict.values())
        for obj in _all:
            media = media + obj.media
        return media + vendor('xadmin.widget.selectrelation.js')
