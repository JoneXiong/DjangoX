;(function($){

  $.fn.exform.renders.push(function(f){
    if($.fn.jstree){

      f.find('.admin-m2m-tree:not(.rended)').each(function(){
        var tree_input = $(this);
        var tree = tree_input.jstree({
          "plugins" : [ "themes", "html_data", "checkbox", "ui", "search" ],
          "themes": {
            "theme": "classic",
            "icons": false,
            "url": window.__admin_media_prefix__ + '../common/css/jstree/style.css'
          },
		  "types": {
			  "default" : {
				"icon" : false  // 关闭默认图标
			  },
		  },
          "search": {
            show_only_matches: true
          },
          "checkbox": {
            override_ui: true,
            real_checkboxes: true,
            two_state: true,
            real_checkboxes_names: function(n){
              return [tree_input.attr('name'), $(n[0]).attr('value')];
            }
          }
        })
        .bind('change_state.jstree', function(e, data){
            var li = data.inst.get_selected();
            var arr=new Array();
            for (var i=0; i<li.length; i++){
                arr.push(li[i].getAttribute('label'))
            }
            $(this).parent().prev().children(".filter-option").text(arr.join(', '));
        })
        .bind('check_node.jstree', function(e, data){
          var node = data.args[0];
          var parent = data.inst._get_parent(node);
          if(parent){
            //data.inst.check_node(parent);
          }
        });
        tree_input.addClass('rended');
      });

      f.find('.admin-fk-tree:not(.rended)').each(function(){
        var tree_input = $(this);
        var tree = tree_input.jstree({
          "plugins" : [ "themes", "html_data", "ui", "search" ],
          "themes": {
            "theme": "classic",
            "icons": false,
            "url": window.__admin_media_prefix__ + '../common/css/jstree/style.css'
          },
		  "types": {
			  "default" : {
				"icon" : false  // 关闭默认图标
			  },
		  },
          "search": {
            show_only_matches: true
          }
        })
        .bind('select_node.jstree', function(e, data){
            if ($(this).hasClass('leaf')){
                var node = data.args[0];
                var children = data.inst._get_children(node);
                if (children.length>0){
                    e.preventDefault();
                    e.stopPropagation();
                    return false;               
                }
            }
            var li = data.inst.get_selected();
            $(this).parent().prev().children(".filter-option").text(li[0].getAttribute('label'));
            $(this).parent().prev().prev().val(li[0].value);
        });
        tree_input.addClass('rended');
      })

    }
  });

$(".admin-m2m-tree.dropdown-menu").click(function (e) {
    e.preventDefault();
    e.stopPropagation();
    return false;
});

$('#jstree-search').click(function (e) {
    e.preventDefault();
    e.stopPropagation();
    return false;
});
$('#jstree-search').keyup(function (e) {
    $(".admin-fk-tree,.admin-m2m-tree").jstree("search",$(this).val());
});

})(jQuery)
