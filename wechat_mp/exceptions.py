# -*- coding: utf-8 -*-
"""
@version: python3.6
@author: "Roger Lee"
@license: MIT Licence 
@contact: 704480843@qq.com
@file: exceptions.py
@time: 2018/9/8 11:16
"""


class InvalidAccountOrPassword(Exception):
    """
    登陆账号或者密码错误时的异常
    """
    pass


class ArticlesNotObtainError(Exception):
    """
    当导出公众号的图文列表时，如果没有先搜索图文就导出
    就会触发这个异常
    """
    pass
