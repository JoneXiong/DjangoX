/**
 * @author bh-lay
 * @github https://github.com/bh-lay/iframer/
 * @modified 2015-4-29 1:19
 */
(function (window, document, iframer_factory, utils_factory) {
	var utils = utils_factory(window, document);
    window.iframer = window.iframer || iframer_factory(window, document, utils);
})(window, document, function(window, document, utils) {
        //当前激活状态的 page （PAGE实例化后的对象）
    var private_active_page,
        //最后一次加载的 page （PAGE实例化后的对象）
        private_last_page,
		//记录组件是否已被初始化
        private_isInited = false,
		//主页面域名（包含协议）
		private_page_domain,
		//单页主页面路径
		private_basePage_path,
		//获取url中域名（包含协议）正则 'http://xxx.xx/xxx','https://xxx.xx/xxx','//xxx.xx/xxx'
		private_reg_domain = /^(?:http(?:|s)\:)*\/\/[^\/]+/,
		//由于hash的特殊性，在这里记录是否刷新iframe视图
		private_needRefresh = true,
        //修改title事件
        private_beforeTitleChange,
		private_iframeOnload,
		LOCATION = window.location;
    
	//获取最新的hash
	function getHash(hashStr) {
		return (hashStr || LOCATION.hash || '#!').replace(/^#!/,'')
	}
	/**
     * 修改hash
     *   isSilence: 不需要更新页面
     **/
	function changeHash(url,win,isSilence) {
        private_needRefresh = isSilence ? false : true;
        
		url = hrefToAbsolute(url,(win || window).location.pathname);
		if(url.length < 1) {
			return
		}
		LOCATION.hash = '!' + decodeURIComponent(url);
	}
	/**
	 * 转换各类地址至相对站点根目录地址
	 *	如  '../../blog/cssSkill.html','blog/cssSkill.html'
     *  至  '/xxx/xxx'
	 **/
	function hrefToAbsolute(src,base_path) {
		// 截断域名
		src = src.replace(private_reg_domain,'');

		//符合要求，直接返回src: /blog/cssSkill.html
		if(src.charAt(0) == "/") {
			return src;
		}
		
		base_path = /^[^?#]*\//.exec(base_path)[0];
		//处理 '../'
		if(src.match(/^\.\.\//)) {
			src = src.replace(/\.\.\//g,function() {
				//每匹配到一个“../”，base_path向前退一位
				base_path = base_path.replace(/\/[^\/]*\/$/,'/');
				return '';
			});
		}
		return base_path + src; 
	}
     //是否为不同域名
    function isHrefOutDomain(href) {
        var domain = (href || '').match(private_reg_domain);
		return (domain && domain[0] != private_page_domain) ? true : false;
    }
	/**
	 * 检测链接是为提供给js使用的地址
     *   无地址、 javascript:: 、javascript:void(0)、#
	 **/
	function hrefForScript(href) {
		return (href.length == 0 || href.match(/^(javascript\s*\:|#)/)) ? true : false;
	}
	/**
	 * 链接包含配置排除class
	 **/
	function linkExpectForSpa(link) {
		if(utils.hasClass(link,IFRAMER.expect_class)) {
			return true;
		}
	}
	var onhashchange = (function() {
		var documentMode = document.documentMode,
			supportHashChange = ('onhashchange' in window) && ( documentMode === void 0 || documentMode > 7 );
		if(supportHashChange) {
			return function(callback) {
				window.onhashchange = function(e) {
					callback && callback(getHash());
				};
				callback && callback(getHash());
			}
		}else{
			return function (callback) {
				//记录hash值
				var private_oldHash = LOCATION.hash;
				setInterval(function() {
					var new_hash = LOCATION.hash || '#';
					//hash发生变化
					if(new_hash != private_oldHash) {
						private_oldHash = new_hash;
						callback && callback(getHash(new_hash));
					}
				},50);
				callback && callback(getHash());
			}
		}
	})();
    //抛出异常方法
    var error = (console && console.error) ? console.error : function (message) {
        throw message;
    };
    
    /**
     * 三目运算的抽象
     *   value的类型满足type，则用value，否则用defaults
     *   若有transform，则返回的时候对value进行包装（不处理defaults）
     **/
    function isUseElse(type,value,defaults,transform) {
        return utils.TypeOf(value) == type ? (typeof transform == 'function' ? transform(value) : value) : defaults;
    }
    
    //IFRAMER 主对象
    var IFRAMER = {
        default_url : '/',
        expect_class : null,
        init : function (param) {
			if(top != window) {
				return;
			}
            if(private_isInited) {
                error('iframer should be initialized only once');
            }else{
                var param = param || {};
                if(!param.container) {
                    error('missing arguement "container"');
                }else if(!utils.isDOM(param.container)) {
                    error('arguement "container" must be a dom');
                }else{
                    INIT.call(this,param);
                }
            }
        },
        //承载iframe的dom
        container : null,
        //超时时长设置（毫秒）
        timeout : 10000,
         //修改主页面title
        updateTitle: function (title) {
            if(private_beforeTitleChange) {
                var newTitle = private_beforeTitleChange(title);
                title = isUseElse('string',newTitle,title);
            }
            document.title = title;
        },
        /**
         * 修改页面hash锚点
         *  win为调用者所在的 windows
         */
        jumpTo : changeHash
    };
	//初始化
	function INIT(param) {
		this.container = param.container;
		this.expect_class = isUseElse('string',param.expect_class,'spa-expect-links');
		this.default_url = isUseElse('string',param.default_url,'/',function() {
            return hrefToAbsolute(param.default_url,LOCATION.pathname)
        });
		
		private_iframeOnload = isUseElse('function',param.iframeOnload,null);
		private_beforeTitleChange = isUseElse('function',param.beforeTitleChange,null);
		private_basePage_path = LOCATION.pathname;
		private_page_domain = LOCATION.protocol + '//' + LOCATION.host;
		
		var firstHash = (LOCATION.hash || '#!').replace(/^#\!/,'');
        
		LOCATION.hash = '!' + (firstHash.length ? hrefToAbsolute(firstHash,LOCATION.pathname) : this.default_url);
		setTimeout(function() {
			//监听hashchange事件
			onhashchange(function(url) {
                // 不需要更新 iframe 结束运行
				if(!private_needRefresh) {
                    private_needRefresh = true;
					return;
				}
				url = url || IFRAMER.default_url;
                
                //若 URL 为单页基础 URL，转为默认 URL
				if(url == private_basePage_path) {
					url = IFRAMER.default_url;
					changeHash(url);
				}else{
                    //
                    if(private_last_page) {
                        if(private_last_page.url == url) {
                            //同一 URL 不处理，避免重复点击
                            return
                        } else if(private_last_page.status == 'loading') {
                            //不同 URL ，且上一页面正在加载中，销毁上一个页面
                            private_last_page.destroy();
                        }
                    }
					private_last_page = new PAGE(url,{
                        onLoad : function() {
                            //销毁老的页面
                            private_active_page && private_active_page != this && private_active_page.destroy();
                            //更新当前iframe标记
                            private_active_page = this;
                        },
                        onTimeout : function() {
                            if(private_active_page) {
                                //超时，且当前有页面，销毁自己
                                this.destroy();
                                
                                //静默修改地址                                
                                changeHash(private_active_page.url,private_active_page.iframe.contentWindow,true);
                            }
                        }
                    });
				}
			});
		});

		private_isInited = true;
	}
	
	/**
     * 创建新的页面
     *
     **/
	function PAGE(url,param) {
        var me = this,
            onLoad = isUseElse('function',param.onLoad,null),
            onTimeout = isUseElse('function',param.onTimeout,null),
            iframe = document.createElement('iframe');
        
        this.iframe = iframe;
        this.status = 'loading';
        this.url = url;
        
		iframe.src= url;
		iframe.frameBorder = 0;
        if(private_active_page) {
			utils.css(iframe,{
				height: 0
			});
		}
        IFRAMER.container.appendChild(iframe);
		
		//加载超时（取消加载）
		me.timeoutListener = setTimeout(function() {
			onTimeout && onTimeout.call(me);
		},IFRAMER.timeout);
		//监听iframe load事件
        utils.bind(iframe,'load',function() {
            me.status = 'loaded';
			clearTimeout(me.timeoutListener);
            
            onLoad && onLoad.call(me);
			utils.css(iframe,{
				height: ''
			});
			//
			try{
				//子window对象
				var iWindow = iframe.contentWindow,
					iDoc = iframe.contentWindow.document;
				//主动触发iframe加载回调
				private_iframeOnload && private_iframeOnload.call(iDoc,iWindow,iDoc);

				//监听事件
				bindEventsForIframe(iWindow,iDoc);
			}catch(e) {}
		});
	}
    PAGE.prototype.destroy = function() {
        clearTimeout(this.timeoutListener);
        this.iframe && utils.removeNode(this.iframe);
        this.iframe = this.status = this.url = null;
    };
    //绑定iframe事件
    function bindEventsForIframe(iWindow,iDoc) {
        //获取当前iframe内的url
		var newPath = decodeURIComponent(iWindow.location.href.replace(private_reg_domain,''));
		//应对服务器可能重定向,或内部跳转
		if(newPath != getHash()) {
			//若重定向到了最外层地址基础页面
			if(newPath == private_basePage_path) {
				//跳转至默认页
				changeHash(IFRAMER.default_url);
			}else{
				//静默修改地址
				changeHash(iWindow.location.href,iWindow,true);
			}
		}

		//更新网页标题
		IFRAMER.updateTitle(iWindow.document.title);
        
		//处理非单页链接跳转问题
		utils.bind(iWindow.document,'mousedown','a',function(evt) {
			var href = this.getAttribute('href') || '',
				target = this.getAttribute('target');
			
			//若链接指向了最外层地址，更改为默认地址
			if(href == private_basePage_path) {
				this.setAttribute('href',IFRAMER.default_url);
			}
            //定义排除在SPA外的class，跨域名的链接，加上_blank
			if(linkExpectForSpa(this) || isHrefOutDomain(href)) {
				this.setAttribute('target','_blank');
			}
		});
		//监听iframe内 单页按钮点击事件
		utils.bind(iWindow.document,'click','a' ,function(evt) {
			var href = this.getAttribute('href') || '';
            //不处理for script、跨域、定义排除在spa外的链接
			if(hrefForScript(href) || isHrefOutDomain(href) || linkExpectForSpa(this)) {
				return;
			}

			IFRAMER.jumpTo(href,iWindow);
			//阻止浏览器默认事件
			var evt = evt || iWindow.event; 
			if (evt.preventDefault) {
				evt.preventDefault(); 
			} else { 
				evt.returnValue = false; 
			}
		});
    }
    
    return IFRAMER;
},function (window,document) {
	/**
	 * 判断对象类型
	 * string number array
	 * object function 
	 * htmldocument
	 * undefined null
	 */
	function TypeOf(obj) {
		return Object.prototype.toString.call(obj).match(/\s(\w+)/)[1].toLowerCase();
	}
	
	/**
	 * 检测是否为数字
	 * 兼容字符类数字 '23'
	 */
	function isNum(ipt) {
		return (ipt !== '') && (ipt == +ipt) ? true : false;
	}
	
	/**
 	 * 遍历数组或对象
	 * 
	 */
	function each(arr,fn) {
		//检测输入的值
		if(typeof(arr) != 'object' || typeof(fn) != 'function') {
			return;
		}
		var Length = arr.length;
		if( isNum(Length) ) {
			for(var i=0;i<Length;i++) {
				if(fn.call(this,i,arr[i]) === false) {
					break
				}
			}
		}else{
			for(var i in arr) {
				if (!arr.hasOwnProperty(i)) {
					continue;
				}
				if(fn.call(this,i,arr[i]) === false) {
					break
				}
			}
		}
	}
	
	/**
	 * 对象拷贝
	 *
	 */
	function clone(fromObj,toObj) {
		each(fromObj,function(i,item) {
			if(typeof item == "object") {   
				toObj[i] = item.constructor==Array ? [] : {};
				
				clone(item,toObj[i]);
			}else{
				toObj[i] = item;
			}
		});
		
		return toObj;
	}
	/**
	 * 判断dom是否拥有某个class
	 */
	function hasClass(dom,classSingle) {
		return dom.className && dom.className.match(new RegExp('(\\s|^)' + classSingle + '(\\s|$)')) || false;
	}
	
	//获取样式
	function getStyle(elem, prop) {
		var value;
		prop == "borderWidth" ? prop = "borderLeftWidth" : prop;
		if (elem.style[prop]) {
			value = elem.style[prop];
		} else if(document.defaultView) {
			var style = document.defaultView.getComputedStyle(elem, null);
			value = prop in style ? style[prop] : style.getPropertyValue(prop);
		} else if (elem.currentStyle) {
			value = elem.currentStyle[prop];
		}
		
		
		if (/\px$/.test(value)) {
			value = parseInt(value);
		}else if (isNum(value) ) {
			value = Number(value);
		} else if(value == '' || value == 'medium') {
			value = 0;
		} else if (value == 'auto') {
			if(prop == 'height') {
				value = elem.clientHeight;
			}else if(prop == 'width') {
				value = elem.clientWidth;
			}
		}
		
		return value;
	}
	

	/**
	 * dom设置样式
	 */
	function setStyle(elem,prop,value) {
		prop = prop.toString();
		if (prop == "opacity") {
			elem.style.filter = 'alpha(opacity=' + (value * 100)+ ')';
			value = value;
		} else if ( isNum(value) && prop != 'zIndex') {
			value = value + "px";
		}
		elem.style[prop] = value;
	}
	//设置css
	function setCss(doms,cssObj) {
		doms = [].concat(doms);
		
		/**
		 * 为css3属性增加扩展
		 */
		each(cssObj,function(key,value) {
			if(key == 'transform' || key == 'transition') {
				each(['webkit','o','moz'],function(i,text) {
					cssObj['-' + text + '-' + key] = value
				});
			}
		});
		each(doms,function(i,dom) {
			each(cssObj,function(key,value) {
				setStyle(dom,key,value);
			});
		});
	}
	
	/**
	 * 事件绑定
	 * elem:节点
	 * type:事件类型
	 * handler:回调
	 */
    var bindHandler = (function() {
		// 标准浏览器
		if (window.addEventListener) {
			return function(elem, type, handler) {
				elem.addEventListener(type, handler, false);
			}
		} else if (window.attachEvent) {
			// IE浏览器
			return function(elem, type, handler) {
				elem.attachEvent("on" + type, handler);
			}
		}
	})();

	/**
	 * 事件解除
	 * elem:节点
	 * type:事件类型
	 * handler:回调
	 */
	var removeHandler = (function() {
		// 标准浏览器
		if (window.removeEventListener) {
			return function(elem, type, handler) {
				elem.removeEventListener(type, handler, false);
			}
		} else if (window.detachEvent) {
			// IE浏览器
			return function(elem, type, handler) {
				elem.detachEvent("on" + type, handler);
			}
		}
	})();
	
	function checkEventForTagname(event,tagName,dom) {
		var target = event.srcElement || event.target;
		while (1) {
			if(target == dom || !target) {
				return false;
			}
			if(target.tagName.toLocaleLowerCase() == tagName) {
				return target;
			}
			
			target = target.parentNode;
		}
	}
	function bind(elem, type,a,b) {
		var className,tagName,fn;
		if(typeof(a) == 'string') {
			fn = b;

            tagName = a;
            callback = function(e) {
                var bingoDom = checkEventForTagname(e,tagName,elem);
                if(bingoDom) {
                    fn && fn.call(bingoDom,e);
                }
            };
		}else{
			callback = a;
		}
		bindHandler(elem,type,callback);
	}
	
    return {
		TypeOf : TypeOf,
		isNum : isNum,
		each : each,
		getStyle : getStyle,
		css : setCss,
		bind : bind,
		clone : clone,
		unbind : removeHandler,
		hasClass : hasClass,
		addClass : function (dom, cls) {
			if (!this.hasClass(dom, cls)) dom.className += " " + cls;
		},
		removeClass : function (dom, cls) {
			if (hasClass(dom, cls)) {
				var reg = new RegExp('(\\s|^)' + cls + '(\\s|$)');
				dom.className = dom.className.replace(reg, ' ');
			}
		},
        isDOM : ( typeof HTMLElement === 'object' ) ? function(obj) {
            return obj instanceof HTMLElement;
        } : function(obj) {
            return obj && typeof obj === 'object' && obj.nodeType === 1 && typeof obj.nodeName === 'string';
        },
		//创建dom
		createDom : function (html) {
			var a = document.createElement('div');
			a.innerHTML = html;
			return a.childNodes;
		},
		//在指定DOM后插入新DOM
		insertAfter : function (newElement, targetElement) {
			var parent = targetElement.parentNode;
			if (parent.lastChild == targetElement) {
				//如果最后的节点是目标元素，则直接追加
				parent.appendChild(newElement);
			} else {
				//插入到目标元素的下一个兄弟节点之前
				parent.insertBefore(newElement, targetElement.nextSibling);
			}
		},
		//移除dom节点
		removeNode : function (elem) {  
			if(elem && elem.parentNode && elem.tagName != 'BODY') {  
				elem.parentNode.removeChild(elem);  
			}  
		},
		//根据class查找元素
		findByClassName : (function() {
			if(typeof(document.getElementsByClassName) !== 'undefined') {
				//支持gEbCN
				return function (dom,classStr) {
					return dom.getElementsByClassName(classStr);
				};
			}else{
				//无奈采用遍历法
				return function (dom,classStr) {
					var returns = [];
					//尝试获取所有元素
					var caches = dom.getElementsByTagName("*");
					//遍历结果
					each(caches,function(i,thisDom) {
						//检查class是否合法
						if(hasClass(thisDom,classStr)) {
							returns.push(thisDom);
						}
					});
					return returns;
				};
			}
		})()
	};
});