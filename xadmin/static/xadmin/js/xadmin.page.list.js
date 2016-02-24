jQuery(function($){
    //full screen btn
    $('.layout-btns .layout-full').click(function(e){
        var icon = $(this).find('i')
        if($(this).hasClass('active')){
            // reset
            $('#left-side, ul.breadcrumb').show('fast');
            $('#content-block').removeClass('col-md-12 col-sm-12 full-content').addClass('col-sm-11 col-md-10');
            icon.removeClass('fa-compress').addClass('fa-expand');
            $(window).trigger('resize');
        } else {
            // full screen
            $('#left-side, ul.breadcrumb').hide('fast', function(){
                $('#content-block').removeClass('col-sm-11 col-md-10').addClass('col-md-12 col-sm-12 full-content');
                icon.removeClass('fa-expand').addClass('fa-compress');
                $(window).trigger('resize');
            });
        }
    });

    $('.layout-btns .layout-normal').click(function(e){
        $('.results table').removeClass('table-condensed');
    });

    $('.layout-btns .layout-condensed').click(function(e){
        $('.results table').addClass('table-condensed');
    });
    
	$('a.for_multi_select').click(function(e){
		var $this = $(this);
		var m_show  = $this.attr("show");
		var m_id = $this.attr("sid");
		opener.dismissRelatedLookupPopup(window,m_id,m_show);
		window.close();
    });
    
    $('#confirm_select').click(function(e){
    	var $this = $(this);
		var id_array=new Array();
		var m_count = 0;
		var checked_list = $('input[name="_selected_action"]:checked');
		if ( !opener.can_multi_select_check(window) && checked_list.length>1){
		  	alert('只能选择一个');
		  	return false;
		}
		checked_list.each(function(){
			var $this = $(this);
			var m_target = $this.parents().filter("tr").find("a.for_multi_select");
			var m_show = m_target.attr("show");
			var m_id = m_target.attr("sid");
			opener.dismissRelatedLookupPopup(window, m_id, m_show);
			m_count ++;
		});
	  if (m_count>0){
	    if ($this.hasClass('select_close')){
	      window.close();
	     }
	  	return true;
	  }else{
	  	alert('请先选择');
	  	return false;
	  }
    });

});