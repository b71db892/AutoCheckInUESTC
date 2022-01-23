#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json
import time

import requests

from logger import logger
from config import wechat_options as options


def _get_token():
    res = requests.get(url=options["token_url"], params={
        "grant_type": 'client_credential',
        'appid': options["appID"],
        'secret': options["appsecret"],
    })
    res = res.json()
    token = res.get('access_token')
    logger.info(f'token update:{token}')
    return token


def push_check_in_ok(user_id, user_name="谁谁谁", text="", tpl_id=options["ok_tpl_id"], redirect_url=''):
    params = {'access_token': _get_token()}
    body = {
        "touser": user_id,
        "template_id": tpl_id,
        "url": redirect_url,
        "data": {
            "datetime": {
                "value": f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}',
                "color": "#173177"
            },
            "user": {
                "value": f'{user_name}',
                "color": "#173177"
            },
            "text": {
                "value": f'{text}',
                "color": "#173177"
            }
        }
    }
    return requests.post(url=options['push_url'], params=params,
                         data=json.dumps(body, ensure_ascii=False).encode('utf-8'))


def push_check_in_failed(user_id, user_name="谁谁谁", text="", tpl_id=options["failed_tpl_id"],
                         redirect_url=''):
    params = {'access_token': _get_token()}
    body = {
        "touser": user_id,
        "template_id": tpl_id,
        "url": redirect_url,
        "data": {
            "datetime": {
                "value": f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}',
                "color": "#ea6f5a"
            },
            "user": {
                "value": f'{user_name}',
                "color": "#ea6f5a"
            },
            "text": {
                "value": f'{text}',
                "color": "#ea6f5a"
            }
        }
    }
    return requests.post(url=options['push_url'], params=params,
                         data=json.dumps(body, ensure_ascii=False).encode('utf-8'))


if __name__ == "__main__":
    wechat_user_id = 'abcabcabcabcabcabcabcabcabc'  #
    push_check_in_ok(wechat_user_id, user_name='名字', text='一些乱码/ h v j j h g j h g')
    push_check_in_failed(wechat_user_id, user_name='另一个名字', text='xFph h g h gii h g h g')
