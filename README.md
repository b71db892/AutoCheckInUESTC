## 严正声明
各组织机构的健康打卡制度是国家疫情防控的重要一环,违反疫情防控有关规定需付刑事责任.此项目仅供学习交流,不可用于违法违规用途.使用本项目造成的任何后果使用者自行承担.
## 快速使用示例
- chrome+chromedriver软件包下载地址：https://www.mediafire.com/folder/ty2a7wlx1kl3h/AutoCheckInUESTC
- Ubuntu 64位(在Ubuntu18.04 和 Uubntu20.04成功运行)
```
# 1. 下载 AutoCheckInUESTC所有代码和chrome97_ubuntu64.tar.gz

# 2. 将chrome97_ubuntu64.tar.gz解压到对应目录
tar -zxvf chrome97_ubuntu64.tar.gz -C AutoCheckInUESTC/chrome97_ubuntu64

# 3. ubuntu 64环境安装示例：
# 使用conda创建名为`env_auto_check_in`的虚拟环境.(需安装Anaconda或Miniconda)
conda create -n env_auto_check_in python=3.7 matplotlib numpy selenium opencv -y
# 激活并进入该环境
conda activate env_auto_check_in
# 使用pip安装undetected_chromedriver
pip install undetected_chromedriver==3.0.3

# 4. 配置打卡账户
# 把账号密码写进`config.py`的`user_list`里,支持多用户一起签到
# 例如
user_list = [
        User('1234567890', 'Mima12345?789', ''),
    ]

# 5. 运行
cd AutoCheckInUESTC
conda activate env_auto_check_in
python main.py

```
- Win10 64位
```
# 1. 下载 AutoCheckInUESTC所有代码和chrome97_win10_64.zip

# 2. 将chrome97_ubuntu64.zip解压到目录`chrome97_win10_64`

# 3. Win10 64环境安装示例：
# 使用conda创建名为`env_auto_check_in`的虚拟环境.(需安装Anaconda或Miniconda)
conda create -n env_auto_check_in python=3.7 matplotlib numpy selenium opencv -y
# 激活并进入该环境
conda activate env_auto_check_in
# 使用pip安装undetected_chromedriver
pip install undetected_chromedriver==3.0.3

# 4. 配置打卡账户
# 把账号密码写进`config.py`的`user_list`里,支持多用户一起签到
# 例如
user_list = [
        User('1234567890', 'Mima12345?789', ''),
    ]

# 5. 运行
conda activate env_auto_check_in
python main.py

```
- Mac OS
```
# 无,欢迎各位大佬折腾
```
## 软件依赖
```angular2html
chrome 浏览器97.x版本,或者最新版
```
项目自带了`windows 10 64位系统`和`ubuntu 64位系统`的chrome浏览器及其驱动,下载后解压到对应目录即可.
此举主要是为了避免chrome版本要和`undetected_chromedriver`包里默认驱动要配套的麻烦.
所以用项目自带的chrome可以不安装`undetected_chromedriver`也不必担心版本问题.
## 环境依赖
- macos平台未测试,请手动使用`pip`安装`undetected_chromedriver`进行调试.
- windows 10 64位请安装以下环境
```angular2html
# 手动配置请安装以下python包
python >= 3.7       # 版本无严格要求
matplotlib          # 版本无严格要求
numpy               # 版本无严格要求
requests            # 版本无严格要求
selenium            # 版本无严格要求
opencv              # 版本无严格要求,这个包在pip安装的时候名字叫`opencv-python`,conda 安装的时候叫做`opencv`
undetected_chromedriver == 3.0.3 # 这个包用pip安装,win10下版本3.0.3通过测试,3.1.3未通过测试
```
- ubuntu 64位请安装以下环境
  
```angular2html
python >= 3.7       # 版本无严格要求
matplotlib          # 版本无严格要求
numpy               # 版本无严格要求
requests            # 版本无严格要求
selenium            # 版本无严格要求
opencv              # 版本无严格要求,这个包在pip安装的时候名字叫`opencv-python`,conda 安装的时候叫做`opencv`
undetected_chromedriver == 3.0.3 # 这个包用pip安装,ubuntu20.04X64 ubuntu18.04X64下版本3.0.3通过测试,3.1.3未通过测试
```
## 配置打卡账户
- 把账号密码写进`config.py`的`user_list`里,支持多用户一起签到
```angular2html
# 例如
user_list = [
        User('1234567890', 'Mima12345?789', ''),
    ]
```
- 推荐结合windows/Linux计划任务功能,实现每天运行一次自动打卡.
## 开启微信通知
这个比较麻烦,而且不是很必要.
运行这个程序初心就是最小化被通知消息打扰的可能性,避免错过其他重要信息.现在通知群管你打不打卡一天都是七八条打卡通知.（我...）
累了累了(大家都不容易).
如果您还需要该打卡程序通过微信告知你程序运行结果的话,请按照以下步骤配置.
- 注册微信公众测试号.

打开以下网址：`https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login` ,点击登录后用微信扫描登陆.然后就能看到`appID`和`appsecret`,先不着急复制.

- 关注

用自己的微信扫码(刚刚那个页面下面有测试号二维码)关注这个测试号，刷新一下网页就会发现用户列表里多了一个用户的昵称和`微信号`等信息,不着急复制,待会会用.

- 新增模板消息

模板消息接口板块有个绿色的新增测试模板按钮,新增两个模板,标题和内容如下:
```angular2html
# 模板1
模板标题：打卡成功
模板内容：时间：{{datetime.DATA}} 用户：{{user.DATA}} {{text.DATA}} 

# 模板2
模板标题：打卡失败
模板内容：时间：{{datetime.DATA}} 用户：{{user.DATA}} {{text.DATA}} 
```
填好后每个模板会有一个唯一ID,就是页面上`模板ID(用于接口调用)`这一列的内容,待会会用.
- 配置编辑`wechat.py`
```angular2html
wechat_options = {
    "appID": "zdfgbnstu86e75jsrte4s56uj",  # 页面上的 appID
    "appsecret": "4w5u6eo76kjahestgjassrxfnzdrhtrjsm",  # 页面上的 appsecret
    "ok_tpl_id": "aewhrzdnjrkystduhtgrctymjtjhgkxmf",  # 这个是标题为'打卡成功'模板的模板id,请替换成自己的
    "failed_tpl_id": "awersfnjndfznrysjrgeazdrsgerjterhjnzrtgj",  # 这个是标题为'打卡失败'模板的模板id,请替换成自己的
}
```
- 务必别忘了配置微信号(open_id)
```angular2html
# 例如
user_list = [
    # 各式：User(user_name, passwd, wechat_openid)
    # 第三项wechat_openid是微信测试号页面上[用户列表]栏里[微信号]的值,是关注测试微信号用户的open_id
    # 不启用WeChat通知功能的话该项留空，填None 或者 '' 都可
    # 例如： User('1234567890', '123456Abc@#$', ''),
        User('1234567890', 'Mima12345?789', 'awegretjsukjyhaegrtsyuykeragvf'),
    ]
```
- 取消注释 `main.py`里关于wechat的语句,行号如下.
```angular2html
8 > # from wechat import push_check_in_ok, push_check_in_failed
18>            # push_check_in_ok(user_id=open_id, user_name=f'{user_name} {obj.checkin_name}', text="")
28>    # push_check_in_failed(user_id=open_id, user_name=f'{user_name}', text=remark)
```
- 测试一下能不能收到消息
```angular2html
# wechat.py 结尾的 __mian__ 代码部分填上要接受消息的微信号（微信测试号页面用户列表里的微信号wechat_openid）
wechat_user_id = 'abcabcabcabcabcabcabcabcabc'
# 运行
python wechat.py
# 然后关注的测试公众号应该会给你发两条模板消息.秒发,几乎没有延迟.
```