# coding=utf-8

from django import forms
from django.forms import Media


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
    
    def __init__(self, admin_view, link, map_dict, attrs=None, using=None):
        self.admin_view = admin_view
        self.link = link
        self.map_dict = map_dict
        super(SelectRelation, self).__init__(attrs)
    
    def value_from_datadict(self, data, files, name):
        link_val = data.get(self.link)
        cur_obj = self.map_dict[link_val]
        return cur_obj.value_from_datadict(data, files, name)
    
    def render(self, name, value, attrs=None):
        link_val = self.get_value(self.link)
        link_val = str(link_val)
        map_list = [( str(k),'%s-%s'%(self.link, id(v)) ) for k,v in self.map_dict.items()]
        _map = dict(map_list)
        if link_val:
            cur_obj = self.map_dict[link_val]
        else:
            cur_obj=None
        _all = set(self.map_dict.values())
        output = []
        for obj in _all:
            if obj==cur_obj:
                output.append( '''<div id="%s-%s">%s</div>'''%(self.link, id(obj), obj.render(name, value, attrs) ) )
            else:
                output.append( '''<div id="%s-%s" style="display: none;">%s</div>'''%(self.link, id(obj), obj.render(name, value, attrs) ) )
        output.append('''
        <script>
            var _map = %s;
            $("#id_%s").change(function(){
                val = $(this).val();
                id = _map[val];
                $('#'+id).show();
                $('#'+id).find("#id_%s").removeAttr("disabled");
                $other = $('#'+id).siblings();
                $other.hide();
                $other.find("#id_%s").attr("disabled","disabled");
            });
        </script>
        '''%(_map,self.link,name,name))
        return ''.join(output)
        
    def get_value(self, key):
        self.form = self.admin_view.form_obj
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
        return media
