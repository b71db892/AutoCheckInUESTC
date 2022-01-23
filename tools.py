import os
import random
import time
import base64
import re
import hashlib
from pathlib import Path
from typing import List, Tuple, NoReturn, Union

import cv2
import numpy as np
from matplotlib import pyplot as plt
from selenium.webdriver import TouchActions
from selenium.webdriver.common.action_chains import ActionChains

from db import DB
from image import IMG
from logger import logger


def kill_cmd():
    pid = os.getpid()
    # pid = os.getppid()
    # 本函数用于中止传入pid所对应的进程
    if os.name == 'nt':
        # Windows系统
        cmd = 'taskkill /pid ' + str(pid) + ' /f'
        try:
            os.system(cmd)
            logger.info(pid, 'killed')
        except Exception as e:
            logger.error(e)
    elif os.name == 'posix':
        # Linux系统
        cmd = 'kill ' + str(pid)
        try:
            os.system(cmd)
            logger.info(pid, 'killed')
        except Exception as e:
            logger.error(e)
    else:
        logger.error('Undefined os.name')


def clean_windows():
    # 关闭所有chrome窗口 和 chromedriver
    cmd = 'powershell -command "Get-Process chrome | ForEach-Object { $_.CloseMainWindow() | Out-Null}"'
    os.system(cmd)
    cmd = 'taskkill /F /im chromedriver.exe'
    os.system(cmd)
    cmd = 'taskkill /F /im chrome.exe'
    os.system(cmd)


# ########### 各种编解码 ###########################
def base64_encode(s) -> str:
    return base64.b64encode(s.encode()).decode()


def base64_decode(s) -> str:
    return base64.b64decode(s).decode()


def str_md5(string) -> str:
    # 求字符串MD5
    md5_value = hashlib.md5()
    md5_value.update(string.encode('utf-8'))
    md5_value_digest = md5_value.hexdigest()
    return md5_value_digest


# ########### 各种格式转换 ###########################
def file_to_src(filename):
    """ 读取并编码图片
    :param filename: str 本地图片文件名
    :return: str 编码后的字符串  eg: src="data:image/gif;base64,R0lGODlhM...H1tXAAAOw=="
    """
    ext = filename.split(".")[-1]
    with open(filename, "rb") as f:
        img = f.read()
    data = base64.b64encode(img).decode()
    src = "data:image/{ext};base64,{data}".format(ext=ext, data=data)
    return src


def src_to_file(src, path=None):
    """解码base64:url图片
    src="data:image/gif;base64,LH1tXAAAO...w=="
    :return: str 保存到本地的MD5文件名
    """
    result = re.search("data:image/(?P<ext>.*?);base64,(?P<data>.*)", src, re.DOTALL)
    if result:
        ext = result.groupdict().get("ext")
        data = result.groupdict().get("data")
    else:
        raise Exception("Do not parse!")
    # img = base64.urlsafe_b64decode(data)
    img = base64.b64decode(data)
    file_name = f"{str(str_md5(src))}.{ext}"
    file_path = os.path.join(Path(__file__).parent, 'imgs')
    if not path and not os.path.exists(file_path):
        os.mkdir(file_path)
    full_abs_path = os.path.abspath(path) if path else os.path.join(file_path, file_name)
    with open(full_abs_path, "wb") as f:
        f.write(img)
    return full_abs_path


def src_to_cv2(src):
    # base64:url图片转cv2图片
    result = re.search("data:image/(?P<ext>.*?);base64,(?P<data>.*)", src, re.DOTALL)
    if result:
        # ext = result.groupdict().get("ext")
        data = result.groupdict().get("data")
    else:
        raise Exception("Do not parse!")

    img = base64.urlsafe_b64decode(data)
    img = cv2.imdecode(np.frombuffer(img, np.uint8), cv2.IMREAD_COLOR)
    return img


def src_to_cv2_ndarray(src):
    #  base64:url图片转cv2图片
    img = src_to_cv2(src)
    img = np.array(img, dtype=np.uint8)
    return img


def cv2_to_src(cv2_img, img_type='png'):
    img = np.array(cv2_img, dtype=np.uint8)
    bits = cv2.imencode('.' + img_type, img)[1].tobytes()
    base64_data = base64.b64encode(bits).decode()
    src = "data:image/{ext};base64,{data}".format(ext=img_type, data=base64_data)
    return src


def cv2_ndarray_to_src(cv2_ndarray, img_type='png'):
    return cv2_to_src(cv2_ndarray, img_type=img_type)


def bgr_to_gray(cv2_ndarray):
    #  转灰度图
    return cv2.cvtColor(cv2_ndarray, cv2.COLOR_BGR2GRAY)


def cv2_ndarray_to_cv2(ndarray):
    ndarray = np.uint8(ndarray)
    b, g, r = ndarray[:, :, 0], ndarray[:, :, 1], ndarray[:, :, 2]
    # 合并通道，形成图片
    img = cv2.merge([b, g, r])
    return img


# ########### 图片显示 ###########################
def imshow(arr, rgb=False) -> NoReturn:
    fig, ax = plt.subplots()
    ax.spines[:].set_visible(False)
    ax.spines.top.set_visible(False)
    if rgb:
        arr = arr.copy() if rgb else arr[:, :, ::-1]
    ax.imshow(arr, cmap=plt.cm.gray)
    plt.show()


# ########### 验证图片处理逻辑 ###########################
def get_blank_window(ndarray, offset=10) -> Tuple[int, int]:
    # 算出验证图片有缺失的高度范围
    # 因为滑块要填在缺口处，所以滑块高度范围就是验证图片缺口范围
    assert len(ndarray.shape) == 3
    assert ndarray.shape[0] >= ndarray.shape[1]
    low, high = min(np.nonzero(ndarray != 0)[0]), max(np.nonzero(ndarray != 0)[0])
    low, high = max(0, low - offset), min(ndarray.shape[0], high + offset)
    return low, high


def is_legal_img(src):
    # 2022.1.11更新,极端离谱的情况下因为不知名的原因图片会只加载一部分,导致没有任何已知图片与之相同
    # 极少数情况下存在图片误判的情况，会把旧图判定为从未出现过的新图（主要是因为判定采用阈值的方法对抗噪声）
    # 如果直接当作新图片存入数据库的话,下次解码该图片的时会崩溃.因此至少要保证存入数据库的图片是正确能解码的.
    try:
        path = os.path.abspath(Path(__file__).parent / f'imgs/tmp.png')
        src_to_file(src, path)
        return True
    except:
        return False


def is_same_img(img1: IMG, img2: IMG) -> bool:
    # 判断两张图片是不是一样的
    # 做法是分别把两张图片缺少的部分删除掉，剩下的是都有的部分。
    # 然后判断一下都有的部分是不是很相似（不可能完全相似，网站加了噪点）
    arr1, arr2 = np.array(img1.cv2_ndarray, dtype=np.uint8), np.array(img2.cv2_ndarray, dtype=np.uint8)
    win1, win2 = [img1.win_start, img1.win_end], [img2.win_start, img2.win_end]
    if arr1.shape != arr2.shape:  # 形状相同
        return False
    h, w, c = arr1.shape
    offset, th = 1, 1  # 边框， 阈值
    # print(h, w, c, offset, th)
    for win in (win1, win2):
        if win[0] < win[1]:
            h1, h2 = max(0, win[0] - offset), min(win[1] + offset + 1, h)  # 1 pix的边框 + 开区间
            arr1[h1:h2, :, :] = 0
            arr2[h1:h2, :, :] = 0
    arr1 = bgr_to_gray(arr1)
    arr2 = bgr_to_gray(arr2)
    # imshow(arr1)
    # imshow(arr2)
    if np.mean(arr1 - arr2) < th:
        return True
    return False


def update_img(base: IMG, new: IMG, db: DB) -> IMG:
    # 拼合两张验证图片
    # 两张相同的照片，缺口不同。我们可以把两张照片都有的部分拼合在一起，得到一张更接近完整答案的验证图片。
    assert base.cv2_ndarray is not None
    assert base.win_start is not None and base.win_end is not None
    assert base.img_id
    assert new.cv2_ndarray is not None
    assert new.win_start is not None and new.win_end is not None
    arr1, arr2 = base.cv2_ndarray.copy(), new.cv2_ndarray.copy()
    win1, win2 = base.win(), new.win()
    # 有效window # 有1像素的边框 # 形状相同
    if win1[1] < win1[0] or win2[1] <= win2[0] or arr1.shape != arr2.shape:
        logger.info(f'合并失败{arr1.shape}:{win1} {arr2.shape}:{win2}')
        return base.copy()
    # h, w, c = arr1.shape
    if win1[0] == -1 and win1[1] == -1:  # 已经全图，无需合并
        logger.info(f'base_img is already ground truth.')
        return base.copy()
    # 缺失区间求交集
    elif win2[1] < win1[0] or win2[0] > win1[1]:
        # 空集，本次可补全
        #  base         0     1
        #  new  0    1  ------   0      1
        h1, h2 = win1
        arr1[h1:h2 + 1, :, :] = arr2[h1:h2 + 1, :, :]  # 左闭右开
        logger.info(f'base_img is updated to ground truth!')
        win = [-1, -1]
        cv2_ndarray = arr1.copy()
        cv2_img = cv2_ndarray_to_cv2(cv2_ndarray)
        base64_src = cv2_to_src(cv2_img)
        md5 = str_md5(base64_src)
        win_start, win_end = win
        db.update_cooked_img(base.img_id, md5, base64_src, win)
        img = base.copy(md5=md5, base64_src=base64_src, win_start=win_start, win_end=win_end,
                        cv2_ndarray=cv2_ndarray, cv2_img=cv2_img)
        # imshow(arr1)
        file_path = os.path.join(Path(__file__).parent, 'imgs')
        if not os.path.exists(file_path):
            os.mkdir(file_path)
        full_abs_path = os.path.join(file_path, f'{img.md5}.png')
        cv2.imwrite(full_abs_path, img.cv2_img)
        logger.info(f'ground truth is saved to `{full_abs_path}`')
        return img
    elif win1[0] < win2[0] <= win1[1]:  # 补一半
        #  base        0        1
        #  new         ----0        1
        h1, h2 = win1[0], win2[0] - 1
        arr1[h1:h2 + 1, :, :] = arr2[h1:h2 + 1, :, :]  # 左闭右开
        win = [win2[0], win1[1]]
        cv2_ndarray = arr1.copy()
        cv2_img = cv2_ndarray_to_cv2(cv2_ndarray)
        base64_src = cv2_to_src(cv2_img)
        md5 = str_md5(base64_src)
        win_start, win_end = win
        db.update_cooked_img(base.img_id, md5, base64_src, win)
        img = base.copy(md5=md5, base64_src=base64_src, win_start=win_start, win_end=win_end,
                        cv2_ndarray=cv2_ndarray, cv2_img=cv2_img)
        return img
    elif win1[0] <= win2[1] < win1[1]:  # 补一半
        #  base        0        1
        #  new   0         1-----
        h1, h2 = win2[1] + 1, win1[1]
        arr1[h1:h2 + 1, :, :] = arr2[h1:h2 + 1, :, :]  # 左闭右开
        win = [win1[0], win2[1]]
        cv2_ndarray = arr1.copy()
        cv2_img = cv2_ndarray_to_cv2(cv2_ndarray)
        base64_src = cv2_to_src(cv2_img)
        md5 = str_md5(base64_src)
        win_start, win_end = win
        db.update_cooked_img(base.img_id, md5, base64_src, win)
        img = base.copy(md5=md5, base64_src=base64_src, win_start=win_start, win_end=win_end,
                        cv2_ndarray=cv2_ndarray, cv2_img=cv2_img)
        return img
    elif win1[0] == win2[0] and win1[1] == win2[1]:
        logger.info(f"完全一致，离大谱了")
        return base.copy()
    elif win2[0] <= win1[0] <= win1[1] <= win2[1]:
        logger.info(f"无用垃圾图，中奖了")
        return base.copy()
    else:
        raise Exception('WTF?')


def calculator_up_to_left(cooked: IMG, new: IMG, block: IMG) -> int:
    # 计算滑块要在验证图片上从左往右滑动多少个像素。
    # 处理方法是在仅有的条件下（有完整原图或者残缺原图）把验证图片上滑块有可能划过的一整个长条区域切割出来，
    # 每次把滑块从长条区域上向右滑动一个像素然后和该长条区域做减法，如果位置正确理论上会有一个位置相减后有非常多值为0的像素点。
    # 从头滑到尾，尽最大可能对比出滑块和图中那个位置的像素最相似。（不可能完全像，所以使用灰度图和阈值减少误差）
    assert cooked.cv2_ndarray is not None
    assert cooked.win_start and cooked.win_start
    assert new.cv2_ndarray is not None
    assert new.win_start and new.win_end
    assert block.cv2_ndarray is not None
    assert block.win_start and block.win_end
    # 转为灰度图
    img1 = cv2.cvtColor(cooked.cv2_ndarray, cv2.COLOR_BGR2GRAY)
    img2 = cv2.cvtColor(new.cv2_ndarray, cv2.COLOR_BGR2GRAY)
    img12 = None
    img3 = cv2.cvtColor(block.cv2_ndarray, cv2.COLOR_BGR2GRAY)
    # 把block方块切出来
    zeros = np.zeros_like(img3)
    zeros[np.nonzero(img3)] = 127  # 1~255 都可
    img3 = zeros[block.win_start: block.win_end + 1, :]

    if cooked.win_start == cooked.win_end == -1:  # 完整原图
        img12 = img1 - img2  # 忽略uint8的溢出
        img12 = img12[block.win_start: block.win_end + 1:]  # 切出来需要做验证的横条
        img12[np.nonzero(img12)] = 1  # 后面做元素乘法, 做01化处理
    elif cooked.win_start == new.win_start and cooked.win_end == new.win_end:  # 抽奖重复？
        img12 = img1 - img2  # 忽略uint8的溢出
        img12 = img12[block.win_start: block.win_end + 1:]  # 切出来需要做验证的横条
        img12[np.nonzero(img12)] = 1  # 后面做元素乘法, 做01化处理
    else:  # 有缺陷原图
        img12 = img1 - img2  # 忽略uint8的溢出
        img12[cooked.win_start: cooked.win_end + 1:] = 0  # 去掉cooked的缺口影响
        img12 = img12[block.win_start: block.win_end + 1:]  # 切出来需要做验证的横条
        img12[np.nonzero(img12)] = 1  # 后面做元素乘法, 做01化处理
    # 滑动窗口相乘，找最大重叠的位置
    # print(img12.shape, img3.shape)  # h, w
    block_width = img3.shape[-1]
    background_width = img12.shape[-1]
    # w 从 0 到 background_width - block_width (包括)
    product_results = []
    # for w in tqdm.trange(0, background_width - block_width + 1, ascii=True):
    for w in range(0, background_width - block_width + 1):
        tmp = np.sum(img3 * img12[:, w:w + block_width])
        product_results.append(tmp)

    dis = int(np.argmax(product_results))
    return dis


def get_distance(img1: IMG, img2: IMG, true_width: int, db: DB) -> int:
    """
    计算屏幕上需要滑动的真实距离
    :param img1: 本次验证图片，来自网页
    :param img2: 本次的滑块图片，来自网页
    :param true_width: 验证图片在屏幕上显示出来的真实宽度
    :param db: 数据库
    :return: 需要滑动的真实距离
    """
    assert true_width > 100
    distance = random.randint(50, true_width - 50)

    def process_img(img: IMG, ):
        assert img.base64_src
        img.md5 = str_md5(img.base64_src)
        img.cv2_img = src_to_cv2(img.base64_src)
        img.cv2_ndarray = np.array(img.cv2_img, dtype=np.uint8)

    process_img(img1)
    process_img(img2)
    img1.win(get_blank_window(img2.cv2_ndarray, offset=10))
    img2.win(get_blank_window(img2.cv2_ndarray, offset=0))
    cooked_img = search_cooked_img(img1, db)
    if cooked_img:
        cooked_img = update_img(cooked_img, img1, db)
        # imshow(cooked_img.cv2_ndarray)
        distance = calculator_up_to_left(cooked_img, img1, img2)
        distance = int(distance / img1.cv2_ndarray.shape[1] * true_width)
        # # 保存 img1, img2. 也可以不存,节约一点点点空间
        # db.save_raw_img(img1.md5, img1.base64_src, img1.win(), cooked_img.img_id)
        # img1.id = img2.raw_id = db.get_raw_img_id(img1.md5)
        # db.save_block_img(img2.md5, img2.base64_src, img1.id)
    else:
        logger.info(f"没找到cooked img, random大法")
        # img1 存入 COOKED_IMGS 这部分一定是新图片,必须要存起来
        if is_legal_img(img1.base64_src) and is_legal_img(img2.base64_src):
            db.save_cooked_img(img1.md5, img1.base64_src, img1.win())
            img1.cooked_id = db.get_cooked_img_id(img1.md5)
            img1_path = os.path.abspath(Path(__file__).parent / f'imgs/new_img1_{time.strftime("%Y%m%d%H%M%S")}.png')
            src_to_file(img1.base64_src, path=img1_path)
            logger.info(f'本次无法判断(图片保存为): {img1_path}')
            # img1 存入 RAW_IMGS
            db.save_raw_img(img1.md5, img1.base64_src, img1.win(), img1.cooked_id)
            img1.id = db.get_raw_img_id(img1.md5)
            # img2 存入 BLOCK_IMGS
            img2.raw_id = img1.id
            db.save_block_img(img2.md5, img2.base64_src, img2.raw_id)
            img2_path = os.path.abspath(Path(__file__).parent / f'imgs/new_img2_{time.strftime("%Y%m%d%H%M%S")}.png')
            src_to_file(img2.base64_src, path=img2_path)
            logger.info(f'本次无法判断(滑块保存为): {img2_path}')
        else:
            logger.warning('图片加载不全, 无法存储.')
            logger.debug(f'img1 src:{img1.base64_src}')
            logger.debug(f'img2 src:{img2.base64_src}')

    return distance


def get_track(dis) -> List[int]:
    # 获取滑动轨迹
    # 不必要的一个函数，负责把滑块需要移动的距离 X0 分解为一系列小距离的和：X0=X1+X2+X3+...
    # 目的是模拟人手动滑动滑块的时候不是一瞬间滑到底的，而是一个过程。此过程也可用其他函数模拟，不重要了。
    track = []
    mid = dis * 4 / 5  # 设置一个分隔线，之前为匀加速运动，之后为匀减速运动
    current = 0  # 用于记录当前的移动距离
    t = 0.2  # 时间间隔
    v = 0  # 初速度
    while current < dis:
        if current < mid:
            a = 8
        else:
            a = -12
        v0 = v
        v = v0 + a * t
        move = v * t + 1 / 2 * a * t * t
        current += move
        track.append(round(move))
    track[-1] += dis - sum(track)
    return track


# ########### 数据库操作函数 ###########################
def search_cooked_img(img: IMG, db) -> Union[IMG, None]:
    # 查询数据库里是否有和本次验证图片一样的图片（只查询保存拼合图片的数据库表即可）
    for item in db.get_cooked_imgs():
        _img_id, _md5, _base64_src, _win_start, _win_end = item
        cooked_img = IMG(img_id=_img_id, md5=_md5, base64_src=_base64_src, cv2_ndarray=src_to_cv2_ndarray(_base64_src),
                         cv2_img=src_to_cv2(_base64_src), win_start=_win_start, win_end=_win_end)
        if is_same_img(cooked_img, img):
            return cooked_img
    return None


# ########### 其他函数 ###########################
def move_mouse(driver, slider, track, duration=25, mobile=False) -> NoReturn:  # 模拟移动
    # PC端点击移动到指定坐标
    # track = [dis], 是一系列移动距离组成的列表
    # 点击和按住
    if mobile:  # 移动端不方便使用drive驱动移动，使用的是js事件，本代码未使用。
        action = TouchActions(driver)
        action.flick_element(slider, sum(track), 1, 50).perform()
    else:
        ActionChains(driver, duration=duration).click_and_hold(slider).perform()
        # 拖动
        for x in track:
            ActionChains(driver, duration=duration).move_by_offset(xoffset=x, yoffset=0).perform()
            time.sleep(0.05)
        time.sleep(2)
        # 松开鼠标
        ActionChains(driver).release().perform()


def disable_win_cmd_insert_mod():
    #  disable the QuickEdit and Insert mode for the current console
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 128)
    except:
        pass


if __name__ == '__main__':
    d = file_to_src('imgs/d716893d7f139cda3e651877009c47fa.png')
    print(d)
    r = src_to_file(d, 'imgs/abc.png')
    print(r)

    # c = CheckIn('', '')
    print(base64_encode('21222242567890'))
    print(base64_encode('123123123sdf#@$.0'))
