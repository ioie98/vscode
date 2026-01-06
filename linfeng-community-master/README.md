<h1 align="center" style="margin: 30px 0 30px; font-weight: bold;">linfeng-community 开源版</h1>
<h4 align="center">基于SpringBoot+MybatisPlus+Shiro+Quartz+WebSocket+jwt+Redis+Vue+Uniapp的前后端分离的社交论坛问答发帖/BBS项目</h4>

 [官网](https://www.linfengtech.cn) |[用户端演示](https://gitee.com/virus010101/linfeng-community/raw/master/images/er.jpg) | [后台演示](https://dev.linfeng.tech) | [交流群](https://gitee.com/virus010101/linfeng-community/raw/master/images/qrcode.jpg) | [文档](https://www.kancloud.cn/linfengkj/linfeng_community/2754703) | [版本区别](https://www.linfengtech.cn/version/version.html) | [Github](https://github.com/virus010101/linfeng-community) 

#### 1.介绍

林风社交论坛uniapp**小程序/H5/APP版本**是基于SpringBoot，MybatisPlus，Shiro，Quartz，jwt，Websocket，Redis，Vue，Uniapp的前后端分离的社交论坛问答发帖/BBS，SNS项目。 项目分为Uniapp用户端（**兼容H5、微信小程序、APP端**）和Vue后台管理端（包括完整的权限处理）， 基于以下技术栈开发：SpringBoot、MybatisPlus、Shiro、Quartz、jwt、websocket、Redis、Vue、Uniapp(vue2、vue3)、MySQL。

包括：图文帖，长文贴，短视频，圈子，私聊，微信支付（小程序/H5/app），付费贴，积分签到，钱包充值，积分余额兑换，话题标签，抽奖大转盘，手机号邮箱登录，虚拟用户发帖，举报，第三方广告，会员模块，即时通讯IM ，好友模块，投票，打赏，用户经验等级，第三方审核等丰富功能，直接看演示更直观↓↓↓↓↓

***后台前端的代码在 src\main\resources\static\linfeng-community-vue目录下！***

***用户端的前端uniapp(vue2)代码在 src\main\resources\static\linfeng-community-uniapp-ky 目录下！***

***用户端的前端uniapp(vue3)新版代码在 src\main\resources\static\linfeng-community-uniapp3-ky 目录下！***

代码三端均提供开源版供学习（**SQL文件在群文件中**）

**官网**：[林风社交论坛官网](https://www.linfengtech.cn)     



#### 2.软件演示

##### 2.1用户端演示版本

演示站点为标准版（h5、app端输入任意手机号即可注册登录体验）

![移动端H5二维码](https://gitee.com/virus010101/linfeng-community/raw/master/images/er.jpg)

或者  H5端访问：https://h5.linfeng.tech      微信小程序:  搜索”林风bbs“

用户端网页PC版本(新发布的产品)演示：https://pc.linfeng.tech

微信公众号：“林风科技”

| 官网/备用官网                              | https://www.linfengtech.cn                                                                             https://net.linfeng.tech |
| ------------------------------------------ | ------------------------------------------------------------ |
| 管理后台演示地址：                         | https://dev.linfeng.tech                                     |
| 开源版功能清单：                           | https://www.linfengtech.cn/version/version.html              |
| 关注公众号"林风科技"体验微信公众号版本演示 | ![输入图片说明](https://gitee.com/virus010101/linfeng-community/raw/master/images/gongzhonghao.jpg) |



  [查看开源版功能清单](https://www.linfengtech.cn/version/version.html)



##### 2.2移动端效果截图

<img src="https://gitee.com/virus010101/linfeng-community/raw/master/images/showPic11.png"/>



![](https://gitee.com/virus010101/linfeng-community/raw/master/images/showPic12.png)



![](https://gitee.com/virus010101/linfeng-community/raw/master/images/showPic13.png)

![](https://gitee.com/virus010101/linfeng-community/raw/master/images/showPic14.png)

![](https://gitee.com/virus010101/linfeng-community/raw/master/images/showPic15.png)

![](https://gitee.com/virus010101/linfeng-community/raw/master/images/showPic16.png)

##### 2.3后台管理端效果截图

后台管理系统标准版演示站点：

https://dev.linfeng.tech

演示账号：已自带

（**注意**：如果多人同时登录同一账号，已登录在线用户会被挤出）

开源版技术栈：Vue2+ElementUI

标准版技术栈：Vue3+Element-Plus

![](https://gitee.com/virus010101/linfeng-community/raw/master/images/showPic05.png)

![](https://gitee.com/virus010101/linfeng-community/raw/master/images/showPic25.png)

![](https://gitee.com/virus010101/linfeng-community/raw/master/images/showPic06.png)

![](https://gitee.com/virus010101/linfeng-community/raw/master/images/showPic08.png)

![](https://gitee.com/virus010101/linfeng-community/raw/master/images/showPic10.png)

![](https://gitee.com/virus010101/linfeng-community/raw/master/images/showPic23.png)



#### 3.安装教程 

1.  配置数据库和redis。先启动redis，再启动后端api服务
2.  数据库请使用MySQL5.7或以上版本。sql文件请点个star后再加群获取
3.  配置后台前端  先npm install 下载依赖后，再npm run dev即可
4.  用户端代码先utils/config.js下配置后端接口 再npm install 安装依赖，然后在HbuilderX中启动项目
5.  具体配置可以参考文档

**林风社交论坛项目标准版文档地址**：https://www.kancloud.cn/linfengkj/linfeng_community/2754703

**开源版文档**：QQ群文档

项目地址：

https://gitee.com/virus010101/linfeng-community

https://github.com/virus010101/linfeng-community

另一个新项目：**婚恋交友系统**（linfeng-love）开源版仓库：https://gitee.com/yuncoder001/linfeng-love

#### 4.必看说明

1.**后台前端的代码**在 **src\main\resources\static\linfeng-community-vue** 目录下！

2.**用户端的前端uniapp(vue2)代码**在 **src\main\resources\static\linfeng-community-uniapp-ky** 目录下！

**用户端的前端uniapp(vue3)新版代码**在 **src\main\resources\static\linfeng-community-uniapp3-ky** 目录下！

3.**代码三端均发布了开源版**。**演示站点的是标准版，不是开源版。**

**标准版和开源版的区别**：

https://www.linfengtech.cn/version/version.html

开源版效果：

 [点击查看开源版移动端效果图](https://pic.linfeng.tech/test/20241120/35a061d0447d481e86cd647a7dc277a5.gif)

了解更多请查看：

[林风社交论坛官网](https://www.linfengtech.cn) 

或关注微信公众号：“林风科技”

4.SQL文件开源的，在QQ群，开源不易，**请左上角star后备注gitee的用户名加QQ群获取**

群1： 640700429  （2000人已满）

群2： 667859660  （新群）

<img src="https://gitee.com/virus010101/linfeng-community/raw/master/images/qrcode.jpg" style="zoom:25%;" />




#### 5.开源须知

- 开源版仅允许用于个人学习研究使用.


- 禁止将本开源的代码和资源进行任何形式任何名义的改造或出售.


- 限制商用，如果需要商业使用请联系我们，二维码如上.


- 本软件已登记软件著作权（登记号：2025SR0586781、2025SR0731472）.



#### 6.标准版更新记录

**当前版本V1.25.0**

历史更新记录汇总：https://www.linfengtech.cn/authInfo/version.html

****

###### V1.25.0发布

2025.10.20

【新增】1.框架升级：从uniapp vue2全面升级为uniapp vue3

【新增】2.代码范式升级：从Options API全面升级为Composition API

【新增】3.首页瀑布流组件支持纯文字贴

【新增】4.首页瀑布流组件优化图片左右分布计算

【新增】5.微信小程序端支持直接openid登录

【新增】6.管理端支持设置小程序端的登录方式

【新增】7.管理端支持设置小程序端是否开启昵称头像弹框

【新增】8.微信小程序端支持更多页面在非登录状态下访问



###### V1.24.0发布

2025.09.01

【新增】1.发帖优先上传图片减少等待时间

【新增】2.重构升级消息列表页UI

【新增】3.重构系统设置页UI

【新增】4.重构优化文件上传、发帖等后端代码

【优化】5.处理后台角色权限编辑树形控件回显

【优化】6.优化文件类型上传的限制

【优化】7.优化后台图片上传报错提示

【优化】8.优化uniapp端公共样式封装

【优化】9.处理微信小程序IOS端视频暂停声音问题

【优化】10.app端发帖增加相机权限

【优化】11.优化部分页面小程序端登录跳转

###### V1.23.0发布

2025.07.11

【新增】1.全新升级websocket模块

【新增】2.支持集群部署

【新增】3.新增数据库脚本备份定时任务

【新增】4.会员页、经验等级页UI焕新升级

【新增】5.充值页、提现页UI焕新升级

【新增】6.长文专区UI焕新升级

【新增】7.举报模块三个页面UI升级

【优化】8.更新后端所有warning提示的代码

【优化】9.H5端在浏览器打开的路径重定向优化

【优化】10.优化支付精度问题

【优化】11.修改时间格式化规则：超过1个月直接显示年月日

【优化】12.优化话题列表更新样式导致的问题

###### V1.22.0发布

2025.05.28

【新增】1.新增我创建的、我加入的圈子

【新增】2.圈子列表、圈子分类页UI全新升级

【新增】3.话题列表、新增话题页UI全新升级

【新增】4.排行榜页、联系客服页UI全新升级

【新增】5.新的朋友消息通知页UI全新升级

【新增】6.投票贴支持后台管理端查看实时结果

【新增】7.新增背景图后台维护

【新增】8.H5端评论链接跳转

【新增】9.海报生成支持http格式

【新增】10.菜单管理支持序号排序

【优化】11.海报生成同步配置的存储类型

【优化】12.部分maven依赖升级

###### V1.21.0发布

2025.04.07

【新增】1.新增APP版本管理功能

【新增】2.新增minio文件存储

【新增】3.新增社区规范协议

【新增】4.重构升级圈子发布页样式

【新增】5.重构升级圈子编辑页样式

【新增】6.视频封面统一管理

【新增】7.后端全面适配用户PC网页端

【优化】8.后台管理系统侧边栏升级

【优化】9.后台管理系统首页数据统计等优化

【优化】10.隐私和服务协议改为富文本编辑

【优化】11.优化消息已读状态

【优化】12.投票后支持查看自己投票的选项

###### V1.20.0发布

2025.02.21

【新增】1.首页新增帖子列表样式自定义功能

【新增】2.首页新增「最新评论帖子」板块

【新增】3.首页新增帖子类型筛选器

【新增】4.websocket升级为长连接机制

【新增】5.websocket心跳检测全新升级

【新增】6.个人主页新增自定义背景图功能

【新增】7.帖子瀑布流组件全新升级

【新增】8.会员过期检查加入定时任务

【优化】9.帖子表和圈子表索引优化

【优化】10.优化访客 IP 查询

###### V1.19.0发布

2025.01.03

【新增】1.阿里云存储升级为V4签名算法

【新增】2.本地存储配置迁移至后台管理端

【新增】3.后台访客模块新增IP查询和快捷操作

【新增】4.后台话题管理支持新增话题和查询

【新增】5.后台帖子管理支持查看长文内容详情

【优化】6.后台帖子、圈子、账单模块升级

【优化】7.优化评论缓存策略

【优化】8.优化发帖排行榜查询规则

【优化】9.优化圈子作品数量缓存

【优化】10.优化管理端富文本编辑器图片上传

###### **V1.18.0发布**

2024.11.1

【新增】1.新增帖子草稿箱功能

【新增】2.新增单点登录，方便整合其他应用

【新增】3.新增圈子管理员进圈审核提醒

【新增】4.新增余额兑换积分功能

【新增】5.新增抽奖模块自定义奖品类型

【新增】6.封号和禁言用户主页新增警示栏

【优化】7.全新升级系统消息页面样式

【优化】8.全新升级举报模块页面样式

【优化】9.全新升级系统隐私设置页面样式

【优化】10.付费贴提示项优化为更友好方式

【优化】11.优化退出登录后好友模块消息重置

【优化】12.优化后台抽奖图片上传

###### **V1.17.0发布**

2024.9.9

【新增】1.新增本地文件存储

【新增】2.新增发贴/涨粉排行榜

【新增】3.新增小程序部分页面开关约束

【新增】4.新增备案跳转

【优化】5.优化上传文件限制

【优化】6.简化长文编辑器

【优化】7.优化访客ip查询增加备用查询接口

【优化】8.优化瀑布流长度限制

###### **V1.16.0发布**

2024.7.22

【新增】1.新增百度智能云内容审核

【新增】2.新增图片评论功能

【新增】3.新增redis消息队列异步解耦

【新增】4.新增邮箱绑定校验

【新增】5.默认注册头像支持在后台配置

【新增】6.圈内帖子数，热门搜索，话题添加缓存

【新增】7.新增公众号在微信自动登录的配置项

【新增】8.新增支持查看本人非上架帖子

【优化】9.优化帖子瀑布流列表样式

【优化】10.优化修改热门贴查询规则

【优化】11.优化提现相关账单记录

【优化】12.优化帖子和圈子管理后台条件查询

【优化】13.视频贴支持跳转后播放

【优化】14.优化投票贴私密圈和消息清理

【优化】15.优化封装后端代码

###### **V1.15.0发布**

2024.6.3

【新增】1.新增访客统计面板支持IP和活跃用户统计

【新增】2.H5端在PC端显示样式兼容

【新增】3.帖子详情页轮播图支持自适应高度

【新增】4.好友模块设置全局开关

【新增】5.细分用户禁言和用户封号功能

【新增】6.后台消息管理升级,支持消息单独发送

【新增】7.管理端登录日志增加ip城市查询

【新增】8.导航栏和用户菜单批量上下架

【优化】9.帖子列表瀑布流样式全新升级

【优化】10.账户充值、签到等页面样式升级

【优化】11.后台评论管理模块全新升级

【优化】12.优化积分奖励限制规则

【优化】13.优化阿里云海报生成下载

【优化】14.付费贴简介展示在帖子列表页

【优化】15.调整tabbar图标和高度，UI升级

###### **V1.14.0发布**

<u>2024.4.9</u>

【新增】1.微信公众号支持注册后用户无感登录

【新增】2.新增子评论折叠栏，优化子评论查询

【新增】3.首页公告弹框样式重构升级

【新增】4.掉线重连操作改成普通接口确保稳定性

【新增】5.帖子详情内容支持换行解析

【优化】6.账单记录展示备注信息及页面样式优化

【优化】7.优化付费贴跳转充值页面后的交互流程

【优化】8.付费贴详情增加简介栏及小程序端转发优化

【优化】9.优化App端切屏的websocket重连机制

【优化】10.优化小程序端注册连线及首页登录跳转

【优化】11.优化后台前端表单样式等

###### **V1.13.0发布**

<u>2024.2.27</u>

【新增】1.新增微信公众号版本

【新增】2.支持微信公众号静默授权

【新增】3.支持微信公众号支付

【新增】4.新增腾讯短信验证码

【新增】5.IOS小程序端支持关闭虚拟支付开关

【优化】6.优化付费贴转发的简介展示问题

【优化】7.支持后台删贴自主提醒用户

【优化】8.优化搜索，优化后台分页

【优化】9.优化签到查询等



###### **V1.12.0发布**

<u>2023.12.12</u>

【新增】1.新增私密圈子

【新增】2.付费贴增加简介部分

【新增】3.付费贴增加条件开关

【新增】4.新增会员权益动态设置模块

【新增】5.新增邮箱注册接口优化邮箱登录 

【新增】6.新增圈子创建审核开关

【新增】7.新增私密圈子条件开关

【新增】8.支持开启全局评论审核

【新增】9.新增后台人机创建按钮及头像昵称修改

【优化】10.优化投票贴选项重复内容校验

【优化】11.优化后台评论搜索审核及抽奖模块

【优化】12.优化代码枚举、前端样式等



###### **V1.11.0发布**

<u>2023.10.23</u>

【新增】1.新增短视频滑动浏览模块

【新增】2.新增短视频播放源加密保护

【新增】3.新增后台发视频及视频链接上传

【新增】4.集成富文本编辑新增后台发布长文

【优化】5.点赞评论、粉丝关注等模块深度集成Redis实现高效缓存，提升接口性能

【优化】6.优化搜索模块限制搜索频率

【优化】7.后台前端vue3重构相关模块优化

【优化】8.其他细节优化

###### **V1.10.0发布**

<u>2023.9.12</u>

【新增】1.后台前端重构升级为Vue3+Element-Plus

【新增】2.新增适配微信小程序用户隐私协议

【新增】3.新增多种全局自定义加载样式

【新增】4.新增用户端404模块页面跳转

【优化】5.优化websocket心跳机制保持通信长连接

【优化】6.重构升级广场页导航模块支持不限数量

【优化】7.优化登录刷新、优化会员续费



历史更新记录汇总：https://www.linfengtech.cn/authInfo/version.html











