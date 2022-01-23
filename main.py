import sys
import time

from logger import logger
from driver import CheckIn
from tools import base64_encode
from config import user_list
# from wechat import push_check_in_ok, push_check_in_failed


def start(user_name, passwd, open_id):
    remark = ''
    for i in range(5):
        try:
            obj = CheckIn(base64_encode(user_name), base64_encode(passwd), mobile=True, headless=True)
            obj.run()
            logger.info(f'{time.asctime(time.localtime(time.time()))}\n{obj.checkin_name}今日打卡已完成！')
            # push_check_in_ok(user_id=open_id, user_name=f'{user_name} {obj.checkin_name}', text="")
            return 0
        except:
            import traceback
            error_info = traceback.format_exc()
            exc_type, exc_value, exc_traceback_obj = sys.exc_info()
            remark = repr(exc_value) + '\n'
            logger.error(error_info)
        time.sleep(3 * 60)
    logger.info(f'{time.asctime(time.localtime(time.time()))}\n打卡失败。？#%！')
    # push_check_in_failed(user_id=open_id, user_name=f'{user_name}', text=remark)
    return -1


if __name__ == '__main__':
    return_code = []
    for user in user_list:
        return_code.append(start(user.user_name, user.passwd, user.wechat_openid))
    logger.info(f"return code:{return_code}")
    print()
