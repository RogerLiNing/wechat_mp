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

def md5(str):

    m = hashlib.md5()
    m.update(str)
    return m.hexdigest()

def from_timestamp_to_datetime_string(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))