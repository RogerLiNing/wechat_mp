# -*- coding: utf-8 -*-
"""
@version: python3.6
@author: "Roger Lee"
@license: MIT Licence 
@contact: 704480843@qq.com
@file: client.py
@time: 2018/9/8 11:16
"""
from wechat_mp.utils import *
from wechat_mp.exceptions import *
from wechat_mp.models import *
import re
import random
import requests
import urllib.parse
from PIL import Image
from io import BytesIO
import time
import json
import logging
import os
from tqdm import tqdm
from threadpool import *

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(threadName)s:%(thread)d] [%(name)s:%(lineno)d] [%(module)s:%(funcName)s] [%(levelname)s]- %(message)s')

console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger = logging.getLogger('wechat_mp')
logger.addHandler(console)
logger.propagate = False


class Wechat:
    """
    主要的API操作程序，用来登陆和调用API方法

    :param email: 登陆微信后台的邮箱
    :type email: str
    :param password: 登陆密码
    :type passowrd: str
    :param enable_cookies: 是否允许保存cookies，避免多次扫码登陆。
    :type enable_cookies: bool
    """

    def __init__(self, email, password, enable_cookies=False):
        self.email = email
        self.passowrd = password
        self.enable_cookie = enable_cookies
        self._base_url = 'https://mp.weixin.qq.com'
        self._is_login = False
        self._token = None
        self.session = requests.Session()
        if enable_cookies:
            if not self._check_cookies():
                self._start_login()
        else:
            self._start_login()

    def api_collections(self, name, path):
        """
        统一管理所有运用到的API

        :param name: 自定义名称
        :type name: str
        :param path: API路径
        :type path: str
        :return: 完整API地址
        """
        apis = {
            'login': {
                'start login': '/cgi-bin/bizlogin?action=startlogin',
                'post login': '/cgi-bin/bizlogin?action=login',
                'check login': '/cgi-bin/loginqrcode?action=ask&token=&lang=zh_CN&f=json&ajax=1',
                'redirect url': '/cgi-bin/bizlogin?action=validate&lang=zh_CN&account={0}',
                'qrcode url': '/cgi-bin/loginqrcode?action=getqrcode&param=4300&rd={0}'
            },
            'search': {
                'search account': '/cgi-bin/searchbiz?action=search_biz&token={0}&lang=zh_CN&f=json&ajax=1&random={1}',
                'article list': '/cgi-bin/appmsg?token={0}&lang=zh_CN&f=json&ajax=1&random={1}&action=list_ex&type=9'
            },
            'template': {
                'get single template detail': '/advanced/tmplmsg?action=tmpl_preview&t=tmplmsg/preview&id={0}&token={1}&lang=zh_CN',
                'get template list xhr':'/advanced/tmplmsg?action=tmpl_store&t=tmplmsg/store&token={0}&lang=zh_CN'
            }
        }

        return self._base_url + apis[name][path]

    def _check_cookies(self):
        """
        检查本地保存的cookies是否有效

        :return: bool
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3218.0 Safari/537.36',
            'Origin': 'https://mp.weixin.qq.com',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded;charset="UTF-8"',
            'Accept': '*/*',
            'Referer': 'https://mp.weixin.qq.com/'}
        file_exist = os.path.exists("cookies.txt")
        if not file_exist:
            f = open('cookies.txt', 'w')
            f.close()
            return False

        with open('cookies.txt', 'r') as f:
            try:
                cookies = json.load(f)
                for k, v in cookies.items():
                    self.session.cookies.set(k, v)
            except json.decoder.JSONDecodeError:
                return False

        response = self.session.get('https://mp.weixin.qq.com/', cookies=cookies, headers=headers)
        find_token = re.findall(r'&token=(\d+)', response.text)
        if find_token:
            self._is_login = True
            self.token = find_token[0]
            logger.info("本地cookies有效，无需再次登陆")
            return True
        else:
            logger.info("本地cookies无效，需重新登陆")
            return False

    def _start_login(self):
        """
        该方法是登陆的第一步，先post登陆邮箱和密码
        成功的话，会进入验证二维码页面

        :return: None
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3218.0 Safari/537.36',
            'Origin': 'https://mp.weixin.qq.com',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded;charset="UTF-8"',
            'Accept': '*/*',
            'Referer': 'https://mp.weixin.qq.com/'}

        data = {'username': self.email,
                'pwd': md5(self.passowrd[0:16].encode('utf-8')),
                'imgcode': '',
                'f': 'json',
                'token': '',
                'lang': 'zh_CN',
                'ajax': 1}

        api = self.api_collections('login', 'start login')
        response = self.session.post(api, headers=headers, data=data)
        logger.info("开始模拟登陆 账号 %s", self.email)
        if response.status_code == 200:
            base_resp = response.json().get('base_resp')
            if base_resp and base_resp['ret'] == 200023:
                raise InvalidAccountOrPassword(f"账号：{self.email} 或者 密码：{self.passowrd} 不正确")
            elif base_resp and base_resp['ret'] == 200008:
                self._verify_qrcode(headers)
            elif base_resp and base_resp['ret'] == 0:
                self._verify_qrcode(headers)

    def _verify_qrcode(self, headers):
        """
        获取验证二维码，显示后监控是否扫码

        :param headers: 请求报文
        :return:
        """
        """{"base_resp":{"err_msg":"ok","ret":0},"redirect_url":"/cgi-bin/bizlogin?action=validate&lang=zh_CN&account=nnjz%40jiexiaochina.com"}"""
        redirect_url = self.api_collections('login', 'redirect url').format(urllib.parse.quote(self.email))
        # 跳转二维码扫码页面
        logger.info("跳转二维码扫码页面")
        response = self.session.get(redirect_url, headers=headers)

        # 获取二维码图片，显示后等待扫码
        qrcode_url = self.api_collections('login', 'qrcode url').format(random.randint(200, 999))
        response = self.session.get(qrcode_url, headers=headers)

        image = Image.open(BytesIO(response.content))
        image.show()
        logger.info("已经获取二维码图片并显示，等待扫码")
        self._check_scan_qrcode()

    def _check_scan_qrcode(self):
        """
        不断地检测是否扫码并确认登陆了
        :return:
        """
        logger.info("开始检查二维码是否被扫和是否已确认")
        while not self._is_login:
            time.sleep(2)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3218.0 Safari/537.36',
                'Origin': 'https://mp.weixin.qq.com',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded;charset="UTF-8"',
                'Accept': '*/*',
                'Referer': 'https://mp.weixin.qq.com/'}
            check_url = self.api_collections('login', 'check login')
            response = self.session.get(check_url, headers=headers, ).json()

            status = response['status']

            if status == 0:
                logger.info("尚未扫码")
            elif status == 4:
                logger.info("已经扫码了，等待确认")
            elif status == 1:
                logger.info("已完成扫码，开始post登陆到微信后台的请求")
                # 确认完成扫码并确认后，post登陆到微信后台的请求
                self._post_login()

    def _post_login(self):
        """
        扫码确认后方可进行这步操作

        :return:
        """
        headers = {'Host': 'mp.weixin.qq.com',
                   'Connection': 'keep-alive',
                   'Origin': 'https://mp.weixin.qq.com',
                   'X-Requested-With': 'XMLHttpRequest',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
                   'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   'Accept': '*/*',
                   'Referer': self.api_collections('login', 'redirect url').format(urllib.parse.quote(self.email)),
                   'Accept-Encoding': 'gzip, deflate, br',
                   'Accept-Language': 'zh-CN,zh;q=0.8', }

        login_url = self.api_collections('login', 'post login')

        data = {"token": "",
                "lang": "zh_CN",
                "f": "json",
                "ajax": "1"}

        # post登陆
        response = self.session.post(login_url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            logger.info("Post登陆成功")
        else:
            logger.info("Post登陆失败")
            return
        # post登陆之后，需要获取token，这个token是调用其他接口的唯一凭证
        # 因为已经登录了，随便访问首页都能得到token，通过正则提取即可
        response = self.session.get('https://mp.weixin.qq.com/', headers=headers)
        find_token = re.findall(r'&token=(\d+)', response.text)
        if find_token:
            self.token = find_token[0]
            self._is_login = True
        else:
            return

        if self.enable_cookie:
            # 保存登陆cookies,避免重复登陆
            cookies = {}
            for k, v in self.session.cookies.get_dict().items():
                cookies[k] = v
            with open('cookies.txt', 'w') as file:
                file.write(json.dumps(cookies))
            logger.info("保存登陆cookies,避免重复登陆")
        logger.info("获取token：%s", self.token)

    def search_account(self, name_or_id, limit=None):
        """
        根据公众号名称或者ID查询公众号列表

        :param name_or_id: 公众号的名称或者微信ID/原始ID
        :type name_or_id: str
        :param limit: 获取多少条查询记录
        :type limit: int
        :return:  :class:`OfficalAccount <wechat_mp.models.OfficalAccount>` 对象列表
        """

        search_api = self.api_collections('search', 'search account').format(self.token, random.randint(200, 999))
        params = {
            'query': name_or_id,
            'begin': 0,
            'count': 5,
        }
        response = self.session.get(search_api, params=params).json()
        accounts = []
        base_resp = response.get('base_resp')

        if base_resp['ret'] == 200013:
            logger.warning("请求频率出现限制，暂停60秒")
            time.sleep(60)
            return self.search_account(name_or_id)

        total = 0
        begin = 0
        if base_resp['ret'] == 0:
            total = response.get('total')

        logger.info("一共有%s个公众号,限制获取%s个公众号", total, limit)
        out_of_limit = False
        while begin < total:
            logger.info("正在获取第%s到第%s个", begin, begin + 5)
            if out_of_limit:
                break
            page_result = self._search_account_pages(search_api, params)
            for account in page_result:
                if limit and limit < len(accounts):
                    out_of_limit = True
                    break
                accounts.append(account)
            begin += 5
            params['begin'] = begin
            time.sleep(3)

        return [OfficalAccount(account, self) for account in accounts]

    def _search_account_pages(self, api, params):
        """
        根据页数不断地进行请求

        :param api: 请求的API
        :param params: 包含起始的参数
        :return: 账号字典列表
        """
        accounts = []
        response = self.session.get(api, params=params).json()
        if response['base_resp']['ret'] == 0:
            account_list = response.get('list')
            accounts += account_list
        return accounts

    def get_templates(self, threads=20, detail=True):
        """
        获取当前公众号的模板消息

        :param threads: 线程数
        :param detail: 是否需要获取模板详情
        :return:
        """
        headers = {
            "Host": "mp.weixin.qq.com",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36")
        }
        api = self.api_collections('template', 'get template list xhr').format(self.token)
        headers["Referer"] = api

        params = {
            'begin':0,
            'count':20,
            'keyword':'',
            'f':'json',
            'ajax':1
        }

        # 先获取所有模板的总数
        response = self.session.get(api, params=params, headers=headers)

        data_str = response.json().get("data")

        total_templates = eval(data_str)['store_tmpl_info']['total_count']

        params['count'] = int(total_templates)
        response = self.session.get(api, params=params, headers=headers)
        if response.status_code == 200:
            if response.json().get('base_resp', ""):
                if response.json().get("base_resp").get("err_msg") != "ok":
                    return

        data_str = response.json().get("data")


        eval_data = eval(data_str)

        templates = eval_data['store_tmpl_info']['store_tmpl']
        template_list = []

        if detail:
            self._get_all_template_details(templates, threads=threads)
            return self.detail_templates
        else:
            template_list = self._get_template_list_with_code(templates)
            return template_list

    def _get_all_template_details(self, templates, threads):
        self.detail_templates = []
        pool = ThreadPool(threads)
        bar = tqdm(total=len(templates))
        bar.set_description("进度条")

        request_list = []
        for template in templates:
            info_dict = {'template': template, 'bar': bar}
            request = makeRequests(self._get_template_details, [info_dict])
            request_list.append(request[0])

        for req in request_list:
            pool.putRequest(req)

        pool.wait()
        bar.close()

    def _get_template_details(self, info_dict):
        template = info_dict['template']
        template_id = template['id']
        bar = info_dict['bar']
        headers = {
            "Host": "mp.weixin.qq.com",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36")
        }
        api = self.api_collections('template', 'get single template detail').format(template_id, self.token)
        response = self.session.get(api, headers=headers)
        html = response.content.decode('utf-8')
        regx = re.compile(r'tmplmsg: (.*)')
        detail_result = re.findall(regx, html)
        if not detail_result:
            return

        detail_dict = eval(detail_result[0])
        bar.update(1)
        template['detail'] = detail_dict

        self.detail_templates.append(template)

    def _get_template_list_with_code(self, templates):
        template_list = []

        # 循环查询行业代码，并生成新的字典放到新的列表template_list
        for template in templates:
            class1 = template['class1'].strip()
            class2 = template['class2'].strip()
            code = self._check_industry_code(class1, class2)
            template_dict = dict(
                id=template['id'],
                title=template['title'],
                industry_code=code
            )
            template_list.append(template_dict)
        return template_list

    def _check_industry_code(self, class1, class2):
        code = ''

        if class1 == "IT科技" and class2 == "互联网|电子商务":
            code = 1
        elif class1 == "IT科技" and class2 == "IT软件与服务":
            code = 2
        elif class1 == "IT科技" and class2 == "IT硬件与设备":
            code = 3
        elif class1 == "IT科技" and class2 == "电子技术":
            code = 4
        elif class1 == "IT科技" and class2 == "通信与运营商":
            code = 5
        elif class1 == "IT科技" and class2 == "网络游戏":
            code = 6
        elif class1 == "金融业" and class2 == "银行":
            code = 7
        elif class1 == "金融业" and class2 == "证券|基金|理财|信托":
            code = 8
        elif class1 == "金融业" and class2 == "保险":
            code = 9
        elif class1 == "餐饮" and class2 == "餐饮":
            code = 10
        elif class1 == "酒店旅游" and class2 == "酒店":
            code = 11
        elif class1 == "酒店旅游" and class2 == "旅游":
            code = 12
        elif class1 == "运输与仓储" and class2 == "快递":
            code = 13
        elif class1 == "运输与仓储" and class2 == "物流":
            code = 14
        elif class1 == "运输与仓储" and class2 == "仓储":
            code = 15
        elif class1 == "教育" and class2 == "培训":
            code = 16
        elif class1 == "教育" and class2 == "院校":
            code = 17
        elif class1 == "政府与公共事业" and class2 == "学术科研":
            code = 18
        elif class1 == "政府与公共事业" and class2 == "交警":
            code = 19
        elif class1 == "政府与公共事业" and class2 == "博物馆":
            code = 20
        elif class1 == "政府与公共事业" and class2 == "政府|公共事业|非盈利机构":
            code = 21
        elif class1 == "医疗护理" and class2 == "医药医疗":
            code = 22
        elif class1 == "医疗护理" and class2 == "护理美容":
            code = 23
        elif class1 == "医疗护理" and class2 == "保健与卫生":
            code = 24
        elif class1 == "交通工具" and class2 == "汽车相关":
            code = 25
        elif class1 == "交通工具" and class2 == "摩托车相关":
            code = 26
        elif class1 == "交通工具" and class2 == "火车相关":
            code = 27
        elif class1 == "交通工具" and class2 == "飞机相关":
            code = 28
        elif class1 == "房地产" and class2 == "房地产|建筑":
            code = 29
        elif class1 == "房地产" and class2 == "物业":
            code = 30
        elif class1 == "消费品" and class2 == "消费品":
            code = 31
        elif class1 == "商业服务" and class2 == "法律":
            code = 32
        elif class1 == "商业服务" and class2 == "广告|会展":
            code = 33
        elif class1 == "商业服务" and class2 == "中介服务":
            code = 34
        elif class1 == "商业服务" and class2 == "检测|认证":
            code = 35
        elif class1 == "商业服务" and class2 == "会计|审计":
            code = 36
        elif class1 == "文体娱乐" and class2 == "文化|传媒":
            code = 37
        elif class1 == "文体娱乐" and class2 == "体育":
            code = 38
        elif class1 == "文体娱乐" and class2 == "娱乐休闲":
            code = 39
        elif class1 == "印刷" and class2 == "打印|印刷":
            code = 40
        elif class1 == "其他" and class2 == "其他":
            code = 41

        return code
