;(function($) {

    function selectR(){
        $('.select-relation').each(function(){
            $this = $(this);
            var name = $this.attr('name');
            var link = $this.attr('link');
            var _map = {};
            $this.children().each(function(){
                _map[$(this).attr('key')] = $(this).text();
            });
            $("select[id^='id_'][id$='"+ link +"']").change(function(){
                val = $(this).val();
                curid = $(this).attr('id');
                pre = curid.replace(link,'');
                id = _map[val];
                $div = $('#'+pre+id);
                $div.show();
                $div.find("input[id^='id_'][id$='"+name+"']").removeAttr("disabled");
                $other = $div.siblings();
                $other.hide();
                $other.find("input[id^='id_'][id$='"+name+"']").attr("disabled","disabled");
            }).trigger("change");
        });
    
    }

    $(function(){
        selectR();
    });
})(jQuery)
