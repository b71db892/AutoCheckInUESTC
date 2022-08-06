from collections import namedtuple

User = namedtuple('User', ['user_name', 'passwd', 'wechat_openid'])

# 需要打卡的用户列表
user_list = [
    # openid是页面上 用户列表 栏里 微信号 的值,是关注测试微信号用户的open_id
    # 不启用WeChat通知功能的话该项留空, 填None 或者 '' 都可
    # 例如： User('1234567890', '123456Abc@#$', ''),
    User('1234567890', '123456Abc@#$', 'abcabcabcabc'),
]

# 微信推送api配置,不使用WeChat推送的话该项可忽略,配置流程在README.MD里有说明
wechat_options = {
    "appID": "abcabcabcabcabc",  # 页面上的 appID
    "appsecret": "abcabcabcabcabcabcabcabcabcabc",  # 页面上的 appsecret
    "ok_tpl_id": "abcabcabcabcabcabcabcabcabcabcabcabcabc",  # 这个是标题为'打卡成功'模板的模板id,请替换成自己的
    "failed_tpl_id": "abcabcabcabcabcabcabcabcabcabcabcabc",  # 这个是标题为'打卡失败'模板的模板id,请替换成自己的
    "push_url": "https://api.weixin.qq.com/cgi-bin/message/template/send?",  # 这行应该不用动
    "token_url": "https://api.weixin.qq.com/cgi-bin/token?"
}

# 使用指定版本的chrome:
# 指定存放chrome.exe 和 chromedriver.exe的文件夹, 可使用绝对路径或者相对于 main.py 文件的相对路径
chrome_path = './chrome'
# chrome_path = 'C:\\Users\\ROOT\\chrome_dir'
# chrome_path = '/root/chrome_dir/'

if __name__ == '__main__':
    pass
