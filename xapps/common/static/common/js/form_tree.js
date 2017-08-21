;(function($){

  $.fn.exform.renders.push(function(f){
    if($.fn.jstree){
      f.find('.admin-tree:not(.rended)').each(function(){
        var tree_input = $(this);
        var tree = tree_input.jstree({
          "plugins" : [ "themes", "html_data", "checkbox", "ui" ],
          "themes": {
            "theme": "classic",
            "url": window.__admin_media_prefix__ + '../common/css/jstree/style.css'
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
        .bind('check_node.jstree', function(e, data){
          var node = data.args[0];
          var parent = data.inst._get_parent(node);
          if(parent){
            data.inst.check_node(parent);
          }
        });
        tree_input.addClass('rended');
      })
    }
  });

})(jQuery)
