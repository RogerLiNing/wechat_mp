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


def encrypt(text):
    """
    传入字符串使用MD5加密
    """
    m = hashlib.md5()
    m.update(text)
    return m.hexdigest()


def from_timestamp_to_datetime_string(timestamp):
    """
    格式化时间戳为日期格式
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


def parse_html(response):
    """
    将HTML内容封装成BeautifulSoup的对象
    """
    # 读取返回的内容，编码使用utf-8，放入变量html
    html = response.content.decode('utf-8')

    # 生成一个BeautifulSoup对象并放入变量soup
    soup = BeautifulSoup(html, 'lxml')

    # 返回BeautifulSoup对象
    return soup
