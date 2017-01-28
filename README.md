# DjangoX
A web GUI suite for Django ORM data or API data management

依托于实际项目和生产环境互联网产品的总结积累，继承和扩展[Xadmin](https://github.com/sshwsfc/xadmin)，DjangoX 努力做 Django 框架的优秀实践项目。

# 特性
1. 经过生产环境大数据量的考验
2. 管理功能强大，接口灵活
3. 继承 xadmin 的强大的功能，将 xadmin 的内部能力API化
4. 扩展xadmin并持续维护，使xadmin不仅能管理 Django ORM 数据还能对接外部非模型数据（如：REST API）

# 使用
1.安装 django 和 crispy_forms 模块
```
easy_install django
easy_install django-crispy_forms
```
推荐组合
- django1.7及以下 + django-crispy_forms==1.4.0
- django==1.8 + django-crispy_forms==1.4.0
- django==1.9 + django-crispy_forms==1.6

2.运行
```
cd example/
. run.sh 
```
windows下则直接双击运行 run.cmd

3.浏览
http://127.0.0.1:81/xadmin/
* 登陆：admin 
* 密码：admin

4.示例网站
[DjangoX示例网站](http://xadmin.ablog.top/xadmin/main.html)
* 登陆：admin 
* 密码：admin

# Screenshots
![info](https://github.com/JoneXiong/DjangoX/raw/master/example/app/static/app/img/show1.png)

![info](https://github.com/JoneXiong/DjangoX/raw/master/example/app/static/app/img/show2.png)

![info](https://github.com/JoneXiong/DjangoX/raw/master/example/app/static/app/img/show3.png)

# Document
[示例启动脚本简析](http://www.oejia.net/blog/2016/01/25/djangox_start_py.html)

[菜单控制与配置](http://www.oejia.net/blog/2016/06/13/djangox_menu.html)

[站点级配置介绍](http://oejia.net/blog/2016/11/21/djangox_site_config.html)

[模型管理功能配置介绍](http://oejia.net/blog/2016/11/29/djangox_admin_conf.html)
