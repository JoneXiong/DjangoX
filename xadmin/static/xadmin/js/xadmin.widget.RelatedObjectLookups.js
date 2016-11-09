// Handles related-objects functionality: lookup link for raw_id_fields
// and Add Another links.

function html_unescape(text) {
    // Unescape a string that was escaped using django.utils.html.escape.
    text = text.replace(/&lt;/g, '<');
    text = text.replace(/&gt;/g, '>');
    text = text.replace(/&quot;/g, '"');
    text = text.replace(/&#39;/g, "'");
    text = text.replace(/&amp;/g, '&');
    return text;
}

// IE doesn't accept periods or dashes in the window name, but the element IDs
// we use to generate popup window names may contain them, therefore we map them
// to allowed characters in a reversible way so that we can locate the correct 
// element when the popup window is dismissed.
function id_to_windowname(text) {
    text = text.replace(/\./g, '__dot__');
    text = text.replace(/\-/g, '__dash__');
    return text;
}

function windowname_to_id(text) {
    text = text.replace(/__dot__/g, '.');
    text = text.replace(/__dash__/g, '-');
    return text;
}
// 打开选择对象的列表页窗口
function showRelatedObjectLookupPopup(triggeringLink) {
    $scope = $(triggeringLink).parent().parent().parent();

    var name = triggeringLink.id.replace(/^lookup_/, '');
    name = id_to_windowname(name);
    var href;
    if (triggeringLink.href.search(/\?/) >= 0) {
        href = triggeringLink.href + '&pop=1';
    } else {
        href = triggeringLink.href + '?pop=1';
    }
    href += '&scope='+ $scope.attr("id");
    var win = window.open(href, name+'@'+$scope.attr("id"), 'height=600,width=1000,resizable=yes,scrollbars=yes');
    win.focus();
    return false;
}

// 清空所有选择
function removeRelatedObject(triggeringLink) {
    $scope = $(triggeringLink).parent().parent().parent();

    var id = triggeringLink.id.replace(/^remove_/, '');
    var elem = $scope.find('#'+id).get(0); //document.getElementById(id);
    var show = $scope.find('#'+id+'_show').get(0);//document.getElementById(id+'_show');
    elem.value = "";
    try{
    	show.innerHTML = "";
    }catch (e) {};
    try{
    	show.value = "";
    }catch (e) {};
}
// 移除单个选择
function removeSingleObject(tar, name, chosenId) {
	var elem = document.getElementById(name);
	var show = document.getElementById(name+'_show');
	var m_val = ','+elem.value+',';
	m_val = m_val.replace(','+chosenId+',', ',');
	if (m_val.length==1){
		elem.value = '';
	}else{
		elem.value = m_val.substring(1,m_val.length-1);
	}
	show.removeChild(tar);
}
// 添加对象
function addObject(elem, show, chosenId, desc){
	
}

// 设置所选的对象
function dismissRelatedLookupPopup(win, chosenId, desc) {
    var li = windowname_to_id(win.name).split('@');
    var name = li[0];
    var scope = li[1];
    //var elem = document.getElementById(name);
    //var show = document.getElementById(name+'_show');
    var elem = $('#'+scope+' #'+name).get(0);
    var show = $('#'+scope+' #'+name+'_show').get(0);
    if (elem.className.indexOf('vManyToManyRawIdAdminField') != -1) {
    	if ( elem.value.split(",").indexOf(''+chosenId)<0 ){
    		if (elem.value){
    			elem.value += ',' + chosenId;
    		}else{
    			elem.value = chosenId;
    		}
	        var span = document.createElement("a");
	        span.setAttribute("class","btn btn-sm");
	        span.onclick=function (){
				removeSingleObject(this,name, chosenId);
	        };
	        var content = document.createTextNode(desc);
	        span.appendChild(content);
	        show.appendChild(span);
    	}
    } else {
        elem.value = chosenId;
        show.value = desc;
    }
    $(elem).change();
    //win.close();
}
// 判断是否可以多选
function can_multi_select_check(win){
	//var name = windowname_to_id(win.name);
	//var elem = document.getElementById(name);
    var li = windowname_to_id(win.name).split('@');
    var name = li[0];
    var scope = li[1];
    var elem = $('#'+scope+' #'+name).get(0);
	return elem.className.indexOf('vManyToManyRawIdAdminField') > -1;
}

function showAddAnotherPopup(triggeringLink) {
    var name = triggeringLink.id.replace(/^add_/, '');
    name = id_to_windowname(name);
    href = triggeringLink.href
    if (href.indexOf('?') == -1) {
        href += '?_popup=1';
    } else {
        href  += '&_popup=1';
    }
    var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
    win.focus();
    return false;
}

function dismissAddAnotherPopup(win, newId, newRepr) {
    // newId and newRepr are expected to have previously been escaped by
    // django.utils.html.escape.
    newId = html_unescape(newId);
    newRepr = html_unescape(newRepr);
    var name = windowname_to_id(win.name);
    var elem = document.getElementById(name);
    if (elem) {
        var elemName = elem.nodeName.toUpperCase();
        if (elemName == 'SELECT') {
            var o = new Option(newRepr, newId);
            elem.options[elem.options.length] = o;
            o.selected = true;
        } else if (elemName == 'INPUT') {
            if (elem.className.indexOf('vManyToManyRawIdAdminField') != -1 && elem.value) {
                elem.value += ',' + newId;
            } else {
                elem.value = newId;
            }
        }
    } else {
        var toId = name + "_to";
        elem = document.getElementById(toId);
        var o = new Option(newRepr, newId);
        SelectBox.add_to_cache(toId, o);
        SelectBox.redisplay(toId);
    }
    win.close();
}
