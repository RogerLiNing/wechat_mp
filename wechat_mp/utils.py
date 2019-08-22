# -*- coding: utf-8 -*-
"""
@version: python3.6
@author: "Roger Lee"
@license: MIT Licence 
@contact: 704480843@qq.com
@file: utils.py
@time: 2018/9/8 11:16
"""

import hashlib
import time

from bs4 import BeautifulSoup


def md5(str):
    m = hashlib.md5()
    m.update(str)
    return m.hexdigest()


def from_timestamp_to_datetime_string(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


def parse_html(response):
    # 读取返回的内容，编码使用utf-8，放入变量html
    html = response.content.decode('utf-8')

    # 生成一个BeautifulSoup对象并放入变量soup
    soup = BeautifulSoup(html, 'lxml')

    # 返回BeautifulSoup对象
    return soup
