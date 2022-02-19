import os
import re
import sys
import time
import datetime
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import tools
from db import DB
from image import IMG
from logger import logger


class CheckIn:
    """
        签到逻辑
        使用的网址是移动设备的签到,和企业微信的签到打卡是同一个网址.
    """

    # sleep 比较多,尽量防止网速或者cpu拖慢页面加载

    def __init__(self, user_name, passwd, mobile=False, headless=False):

        self.user_name = user_name
        self.passwd = passwd
        self.mobile = mobile

        self.db = DB()
        self.checkin_name = '李华'
        self.checkin_date = None
        self.checkin_time = None

        self.driver = self.get_driver(headless, mobile)

        if not mobile:
            self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 15, 0.5)
        logger.info(f'初始化完成...')

    @staticmethod
    def get_driver(headless, mobile):
        from selenium import webdriver
        options = webdriver.ChromeOptions()
        platform = sys.platform
        project_dir = os.path.abspath(Path(__file__).parent)
        if platform.endswith("win32"):
            chrome_dir = os.path.join(project_dir, 'chrome97_win10_64')
            chrome_executable_path = os.path.join(chrome_dir, 'chrome.exe')
            chrome_driver_path = os.path.join(chrome_dir, 'chromedriver.exe')
        elif platform.startswith("linux"):
            chrome_dir = os.path.join(project_dir, 'chrome97_ubuntu64')
            chrome_executable_path = os.path.join(chrome_dir, 'chrome')
            chrome_crashpad_handler_path = os.path.join(chrome_dir, 'chrome_crashpad_handler')
            chrome_driver_path = os.path.join(chrome_dir, 'chromedriver')
            # 直接copy过来的chrome可能会有权限问题, windows server也可能遇到.exe锁定问题,需要在资源管理器右键文件属性解锁
            os.system(f'chmod a+x {chrome_executable_path}')
            os.system(f'chmod a+x {chrome_crashpad_handler_path}')
            os.system(f'chmod a+x {chrome_driver_path}')
        elif platform.endswith("darwin"):  # 暂不支持
            chrome_dir = chrome_executable_path = chrome_driver_path = ''
            logger.warning(f'Unsupported Platform `darwin`.')
        else:
            raise Exception(f"What's your platform?")

        if mobile:
            options.add_experimental_option("mobileEmulation", {"deviceName": "iPhone X"})
        if headless:  # 是否使用无头浏览器（不显示UI界面的浏览器,适合部署在服务器）
            # options.headless = True
            options.add_argument('--headless')
        options.add_argument('--mute-audio')  # 关闭声音
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument("--no-sandbox")
        options.add_experimental_option('excludeSwitches', ['enable-automation'])  # 绕过js检测
        # 在chrome79版本之后，上面的实验选项已经不能屏蔽webdriver特征了
        # 屏蔽webdriver特征
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        # ==================== 寻找 chrome ====================
        if os.path.exists(chrome_executable_path):
            options.binary_location = chrome_executable_path
            options.add_argument(f'--user-data-dir={os.path.join(chrome_dir, "DefaultAppData")}')  # 设置成用户自己的数据目录
            logger.info(f'可找到 "{chrome_executable_path}"')
        else:
            options.add_argument(f'--user-data-dir={os.path.join(project_dir, "./DefaultAppData")}')  # 设置成用户自己的数据目录
            logger.info('找不到 chrome 二进制文件位置,使用系统默认位置')
        # ==================== 寻找 chromedriver ====================
        # 自带的driver是从 undetected_chromedriver 包里copy过来的,可以隐藏chromedriver特征
        if os.path.exists(chrome_driver_path):
            logger.info(f'可找到 "{chrome_driver_path}"')
            # selenium 旧版的代码,新版接口可能不兼容
            return webdriver.Chrome(executable_path=chrome_driver_path, chrome_options=options)
            # selenium 新版的代码
            # from selenium.webdriver.chrome.service import Service
            # return webdriver.Chrome(service=Service(chrome_driver_path), options=options)
        else:
            logger.info('找不到 chromedriver 二进制文件位置, 启用 undetected_chromedriver.')
            import undetected_chromedriver as uc
            return uc.Chrome(options=options)  # version = 97

    def run(self):
        self.mobile_open_website()
        self.mobile_pic_confirm()
        self.mobile_check_in_once()
        # # PC端页面签到停止维护
        # self.open_website()
        # self.pic_confirm()
        # self.check_in_once()

    def open_website(self):
        pass

    def mobile_open_website(self):
        # 打开网址 自动跳转
        logger.info(f'open website...')
        self.driver.get('https://eportal.uestc.edu.cn/jkdkapp/sys/lwReportEpidemicStu/*default/index.do#/dailyReport')
        # 使用js方式输入信息（比chromedriver原生方式快多了）
        self.wait.until(EC.presence_of_element_located((By.ID, "mobileUsername")))
        self.wait.until(EC.presence_of_element_located((By.ID, "mobilePassword")))
        self.wait.until(EC.presence_of_element_located((By.ID, "load")))
        time.sleep(2)
        logger.info(f'input user name ...')
        js_comm = f'document.getElementById("mobileUsername").value="{tools.base64_decode(self.user_name)}"'
        self.driver.execute_script(js_comm)
        time.sleep(2)
        logger.info(f'input pass word ...')
        js_comm = f'document.getElementById("mobilePassword").value="{tools.base64_decode(self.passwd)}"'
        self.driver.execute_script(js_comm)
        time.sleep(2)
        logger.info(f'login...')
        self.wait.until(EC.presence_of_element_located((By.ID, "load")))
        js_comm = 'document.getElementById("load").click()'
        self.driver.execute_script(js_comm)
        time.sleep(2)

    def init_db(self):
        # PC端收集验证图片（无用函数）
        # 无缺口的验证图片使用暴力枚举拼合而成,所以需要一个刷题拼合答案的过程.
        # 在调试期间代码附带的数据库已经初始化好了,此函数一般没啥用.
        for i in range(100):
            # 刷新验证问题
            self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="captcha"]/i[1]')))
            refresh_btn = self.driver.find_element(By.XPATH, '//*[@id="captcha"]/i[1]')
            refresh_btn.click()
            # time.sleep(1)
            # 图片
            self.wait.until(EC.presence_of_element_located((By.ID, "img1")))
            self.wait.until(EC.presence_of_element_located((By.ID, "img2")))
            time.sleep(1)
            img1_base64 = self.driver.find_element(By.ID, 'img1').get_attribute("src")
            img2_base64 = self.driver.find_element(By.ID, 'img2').get_attribute("src")
            # 真实显示框大小
            self.wait.until(EC.presence_of_element_located((By.ID, "captcha")))
            canvas = self.driver.find_element(By.ID, "captcha")
            canvas_width = canvas.size['width']
            # 滑动条
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "slider")))
            slider = self.driver.find_element(By.CLASS_NAME, "slider")

            img1 = IMG(base64_src=img1_base64)
            img2 = IMG(base64_src=img2_base64)

            dis = tools.get_distance(img1, img2, canvas_width, self.db)
            dis = int(dis - slider.size['width'] * 0.5)
            print(dis)

    def pic_confirm(self, ):
        pass

    def mobile_pic_confirm(self, ):
        # 移动端过滑动验证码

        # 11.13更新,今天登陆页面临时取消了滑动图片验证码,导致图片验证环节出错.
        # 更新后若直接登陆成功则自动跳过图片获取验证环节
        # 是否免验证
        try:
            logger.info(f'Check Picture Test')
            tmp_wait = WebDriverWait(self.driver, 5, 0.5)
            tmp_wait.until(EC.presence_of_element_located((By.XPATH, "//div[text()='调整搜索范围']")))
            logger.info(f"We don't need calculate Picture Test Today! Happy Happy EZ Way!")
            return
        except:
            logger.info(f"Calculate Picture Test.")
        # 获取验证图片和滑块图片
        self.wait.until(EC.presence_of_element_located((By.ID, "img1")))
        self.wait.until(EC.presence_of_element_located((By.ID, "img2")))
        time.sleep(5)
        img1_base64 = self.driver.find_element(By.ID, 'img1').get_attribute("src")
        img2_base64 = self.driver.find_element(By.ID, 'img2').get_attribute("src")
        # 获取验证图片真实显示框大小,用于计算真实滑动距离
        self.wait.until(EC.presence_of_element_located((By.ID, "captcha")))
        canvas = self.driver.find_element(By.ID, "captcha")
        canvas_width = canvas.size['width']
        # 滑动条
        time.sleep(2)
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "slider")))
        slider = self.driver.find_elements(By.CLASS_NAME, "slider")[0]
        # 计算滑动距离
        img1 = IMG(base64_src=img1_base64)
        img2 = IMG(base64_src=img2_base64)
        dis = tools.get_distance(img1, img2, canvas_width, self.db)
        logger.info(f"实际距离{dis}")
        # 下面这2行代码不要动,虽然无法解释,但是现在它能用.
        # 理论上滑动距离要减去滑块宽度的一半才对,但是实际debug时发现不用减就能过验证,实在是无法理解,可能是我距离逻辑写的不对.
        # 所以不要动下面这2行代码
        # dis = int(dis - slider.size['width'] * 0.5)
        logger.info(f"减去半个滑块实际距离{dis}")
        track = tools.get_track(dis)
        # 执行向右滑动的动作.移动设备触屏命令不方便使用drive驱动,所以使用js的方式模拟出发滑动事件
        movejs = """
        function sendTouchEvent(x, y, element, eventType) {
            const touchObj = new Touch({
                identifier: Date.now(),
                target: element,
                clientX: x,
                clientY: y,
                pageX: x,
                pageY: y,
                radiusX: 2.5,
                radiusY: 2.5,
                rotationAngle: 10,
                force: 0.5,
            });

            const touchEvent = new TouchEvent(eventType, {
                cancelable: true,
                bubbles: true,
                touches: [touchObj],
                targetTouches: [],
                changedTouches: [touchObj],
                shiftKey: true,
            });

            element.dispatchEvent(touchEvent);
        }

        const myElement = document.getElementsByClassName('slider')[0]
        function move(ele, x, y){
            rect = ele.getBoundingClientRect()
            sendTouchEvent((rect.left + rect.right)/2, (rect.top + rect.bottom)/2, ele, 'touchstart');
            sendTouchEvent((rect.left + rect.right)/2 + x, (rect.top + rect.bottom)/2 + y, ele, 'touchmove');
            sendTouchEvent((rect.left + rect.right)/2 + x, (rect.top + rect.bottom)/2 + y,  ele, 'touchend');
        }

        """
        js_comm = movejs + "move(myElement, {},0);".format(sum(track))
        self.driver.execute_script(js_comm)
        time.sleep(10)

    def check_in_once(self):
        pass

    def mobile_check_in_once(self):
        # 进行一次签到
        if self.is_finished():
            logger.info(f'填完了')
            return
        else:
            logger.info(f'没填')
        logger.info('新增签到记录')
        js_comm = 'document.querySelector("#app > div > div.mint-layout-container.pjcse52gj > ' \
                  'div.mint-fixed-button.mt-color-white.sjarvhx43.mint-fixed-button--bottom-right.' \
                  'mint-fixed-button--primary.mt-bg-primary").click()'
        self.driver.execute_script(js_comm)
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[text()='基本信息']")))
        time.sleep(2)
        logger.info('提交')
        js_comm = 'document.querySelector("#app > div > div > div.mint-layout-container.OPjctwlgzsl > button").click()'
        self.driver.execute_script(js_comm)

        # 11.7日更新：
        # 已经提交过一次的内容默认在下次不用重复填写可直接提交.11.7日新增了疫苗接种情况一栏,程序未设置填写功能,因此打卡出错
        # 不妨每次都检测一次是否有未填写项目的提示.有新提示的话本次打卡失败
        have_tip, middle_tip = False, ''
        try:
            self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "body > div.mint-toast.is-placemiddle")))
            have_tip = True
            time.sleep(0.5)
            middle_tip = self.driver.find_elements(By.CSS_SELECTOR, "body > div.mint-toast.is-placemiddle")[0].text
        except:
            pass
        if have_tip:
            e = f"have_tip:{have_tip}, tips:{middle_tip}"
            logger.error(f"Some tips on the web pages:{e}")
            raise Exception(e)

        logger.info('确定')
        js_comm = 'document.querySelector("body > div.mint-msgbox-wrapper > div > div.mint-msgbox-btns > ' \
                  'button.mint-msgbox-btn.mint-msgbox-confirm.mt-btn-primary").click()'
        self.driver.execute_script(js_comm)
        time.sleep(2)
        if self.is_finished():
            logger.info(f'填完了')
        else:
            logger.warning(f'WTF? 见鬼了？填完了但是没填？')
            raise Exception('Unknown ERROR')
        self.close()

    def is_finished(self):
        # 检查是否签到完成
        try:
            # 11.1日更新：每月第一天获取不到历史打卡记录,所以会出错
            selector = '#app > div > div.mint-layout-container.pjcse52gj > div.cjataj7ar > div > div > div:nth-child(2)'
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            time.sleep(2)
            last_checkin = self.driver.find_elements(By.CSS_SELECTOR, selector)[0]
            last_checkin_text = last_checkin.text
            logger.info(f"last checkin text:{last_checkin_text}")
            rule = r'.*-(?P<name>.*)\n.*\n.*\n.*\n(?P<date>\d{4}-\d{1,2}-\d{1,2})\s(?P<time>\d{1,2}:\d{1,2})'
            res = re.search(rule, last_checkin_text)
            self.checkin_name = res.groupdict()['name']
            self.checkin_date = res.groupdict()['date']
            self.checkin_time = res.groupdict()['time']
            yesterday = (datetime.date.today() + datetime.timedelta(days=-1)).strftime("%Y-%m-%d")
            today = datetime.date.today().strftime("%Y-%m-%d")
            if self.checkin_date == today:
                logger.info(f'{self.checkin_name}已打卡,最后签到时间:{self.checkin_date} {self.checkin_time}')
                return True
            else:
                logger.info(f'{self.checkin_name}未打卡,最后签到时间:{self.checkin_date} {self.checkin_time}')
                return False
        except:
            import traceback
            e = traceback.format_exc()
            logger.warning(e)
            if time.localtime(time.time()).tm_mday == 1:  # 11.1日更新：每月第一天未打卡时获取不到历史打卡记录,则表示今日未打卡, 继续打卡
                return False
            else:
                raise Exception(e)

    def close(self):
        try:
            self.driver.quit()
            logger.info(f'已释放浏览器内存.')
        except:
            pass

    def __del__(self):
        self.close()


if __name__ == '__main__':
    obj = CheckIn('', '')
    obj.close()
    input()
