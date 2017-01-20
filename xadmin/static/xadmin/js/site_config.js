(function(){
	var config = {
		url : window.__admin_path_prefix__ + 'main.html' //注意：这里配置单页所在的路径
	};
	//判断是否为正常用户（区分搜索引擎）
	function isNormalUser(){
		var UA = navigator.userAgent.toLowerCase();
		var UAs = 'baiduspider,googlebot,youdaobot,360spider,msnbot,bingbot,sosospider,yahoo,sogou web spider,sogou orion spider'.split(',');
		for(var i=0,total=UAs.length;i<total;i++){
			if(UA.indexOf(UAs[i]) > -1){
				return false;
			}
		}
		return true;
	}
	if(top == this && isNormalUser()){
		window.location.href = config.url;// + '#!' + location.href; 跳转关键点
	}
}());
