# -*- coding: utf-8 -*-
"""
@version: python3.6
@author: "Roger Lee"
@license: MIT Licence 
@contact: 704480843@qq.com
@file: client.py
@time: 2018/9/8 11:16
"""
import json
import os
import pickle
import re
import urllib.parse
from io import BytesIO

import requests
from PIL import Image
from threadpool import *

from wechat_mp.exceptions import *
from wechat_mp.models import *
from wechat_mp.utils import *

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(threadName)s:%(thread)d] [%(name)s:%(lineno)d] [%(module)s:%(funcName)s] [%(levelname)s]- %(message)s')

console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger = logging.getLogger('wechat_mp')
logger.addHandler(console)
logger.propagate = False


class WeChat:
    """
    主要的API操作程序，用来登陆和调用API方法
    :param email: 登陆微信后台的邮箱
    :type email: str
    :param password: 登陆密码
    :type password: str
    :param enable_cookies: 是否允许保存cookies，避免多次扫码登陆。
    :type enable_cookies: bool
    """

    def __init__(self, email, password, enable_cookies=False):
        self.email = email
        self.password = password
        self.enable_cookies = enable_cookies

        self._base_url = 'https://mp.weixin.qq.com'
        self._is_login = False
        self.token = None
        self.accounts = self._load_accounts() or {}
        pkl_data = self._load_session()
        if pkl_data:
            self.session = pkl_data.get("session")
            self.token = pkl_data.get("token")
        else:
            self.session = requests.Session()
            self.session.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 \
                (KHTML, like Gecko) Chrome/63.0.3218.0 Safari/537.36',
                'Origin': 'https://mp.weixin.qq.com',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded;charset="UTF-8"',
                'Accept': '*/*',
                'Referer': 'https://mp.weixin.qq.com/'
            }
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
                'qrcode url': '/cgi-bin/loginqrcode?action=getqrcode&param=4300&rd={0}',
                "captcha url": "/cgi-bin/verifycode?username={0}&r={1}"
            },
            'search': {
                'search account': '/cgi-bin/searchbiz?action=search_biz&token={0}&lang=zh_CN&f=json&ajax=1&random={1}',
                'article list': '/cgi-bin/appmsg?token={0}&lang=zh_CN&f=json&ajax=1&random={1}&action=list_ex&type=9',
                'search article': '/cgi-bin/operate_appmsg?sub=check_appmsg_copyright_stat',
                'search page': '/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=10&share=1&token={0}&lang=zh_CN'
            },
            'template': {
                'get single template detail': '/advanced/tmplmsg?action=tmpl_preview&t=tmplmsg/preview&id={0}&token={1}&lang=zh_CN',
                'get template list xhr': '/advanced/tmplmsg?action=tmpl_store&t=tmplmsg/store&token={0}&lang=zh_CN'
            }
        }

        return self._base_url + apis[name][path]

    def _start_login(self, img_code=''):
        """
        该方法是登陆的第一步，先post登陆邮箱和密码
        成功的话，会进入验证二维码页面
        :param img_code: 验证码结果
        :return:
        """
        data = {
            'username': self.email,
            'pwd': encrypt(self.password[0:16].encode('utf-8')),
            'imgcode': img_code,
            'f': 'json',
            'token': '',
            'lang': 'zh_CN',
            'ajax': 1
        }

        api = self.api_collections('login', 'start login')
        response = self.session.post(api, data=data)

        logger.info("开始模拟登陆 账号 %s", self.email)
        if response.status_code == 200:
            base_resp = response.json().get('base_resp')
            if base_resp and base_resp['ret'] == 200023:
                raise InvalidAccountOrPassword(f"账号：{self.email} 或者 密码：{self.password} 不正确")
            elif base_resp and base_resp['ret'] == 200008:
                # {"base_resp":{"err_msg":"need verify code","ret":200008}}
                self._verify_captcha()
            elif base_resp and base_resp['ret'] == 0:
                self._verify_qrcode()

    def _verify_captcha(self):
        """验证码识别"""
        api = self.api_collections('login', 'captcha url').format(self.email, int(time.time()) * 1000)
        response = self.session.post(api)
        captcha = Image.open(BytesIO(response.content))
        captcha.show()
        captcha_result = input("输入验证码: ", )
        self._start_login(captcha_result)

    def _verify_qrcode(self):
        """
        获取验证二维码，显示后监控是否扫码
        :return:
        """
        redirect_url = self.api_collections('login', 'redirect url').format(urllib.parse.quote(self.email))
        # 跳转二维码扫码页面
        logger.info("跳转二维码扫码页面")
        response = self.session.get(redirect_url)
        # 响应内容见response/verify_qrcode.json

        # 获取二维码图片，显示后等待扫码
        qrcode_url = self.api_collections('login', 'qrcode url').format(random.randint(200, 999))
        response = self.session.get(qrcode_url)
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
            check_url = self.api_collections('login', 'check login')
            response = self.session.get(check_url).json()

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
        self.session.headers.update({'Referer': self.api_collections('login', 'redirect url').format(urllib.parse.quote(self.email))})

        login_url = self.api_collections('login', 'post login')

        data = {
            "token": "",
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1"
        }

        # post登陆
        response = self.session.post(login_url, data=json.dumps(data))
        if response.status_code == 200:
            logger.info("Post登陆成功")
        else:
            logger.info("Post登陆失败")
            return

        self._get_token(self.session)

    def _get_token(self, session):
        # post登陆之后，需要获取token，这个token是调用其他接口的唯一凭证
        # 因为已经登录了，随便访问首页都能得到token，通过正则提取即可
        response = session.get('https://mp.weixin.qq.com/')
        find_token = re.findall(r'&token=(\d+)', response.text)
        if find_token:
            self.token = find_token[0]
            logger.info("获取token：%s", self.token)
            self._is_login = True
            self.session = session
            self._dump_session()
            return True
        else:
            self._delete_session()
            return False

    def _dump_session(self, filename="./sessions.pkl"):
        """序列化session"""
        if not self.enable_cookies:
            return

        data = {
            "create_time": int(time.time()),
            "session": self.session,
            "email": self.email,
            "password": self.password,
            "token": self.token
        }
        self.accounts.update({self.email: data})
        with open(filename, 'wb') as f:
            pickle.dump(self.accounts, f)

    def _load_accounts(self, filename="./sessions.pkl"):
        if not os.path.exists(filename):
            return {}

        with open(filename, 'rb') as f:
            return pickle.load(f, encoding='utf-8')

    def _load_session(self):
        """反序列化session"""

        account = self.accounts.get(self.email)
        # 检查accounts里有没有 对应的账号
        if account:
            if self._get_token(account.get("session")):
                return account
            else:
                print("登录状态已失效.")
                del self.accounts[self.email]
        return None

    @staticmethod
    def _delete_session(path="./session.pkl"):
        """
        用于删除过期的session,
        如果在搜索公众号或者文章中 返回的响应 invalid session
        则将session.pkl文件删除，置为未登录状态
        :return:
        """
        if os.path.exists(path):
            os.remove(path)

    def search_account(self, name_or_id, limit=0, interval=3):
        """
        根据公众号名称或者ID查询公众号列表

        :param name_or_id: 公众号的名称或者微信ID/原始ID
        :type name_or_id: str
        :param limit: 获取多少条查询记录
        :type limit: int
        :type interval: int 请求时间间隔，秒
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

        begin = 0

        total = response.get('total')
        if limit == 0:
            logger.info("一共搜到%s个公众号,已设置不限制获取数量", total)
            bar = tqdm(total=total)
            limit = total
        else:
            logger.info("一共搜到%s个公众号,已设置限制获取前%s个公众号", total, limit)
            bar = tqdm(total=limit)

        bar.set_description("进度条")
        reach_limit = False

        while not reach_limit:

            page_result = self._search_account_pages(search_api, params)
            if not page_result:
                reach_limit = True
            for account in page_result:
                if len(accounts) >= limit or len(accounts) > total:
                    reach_limit = True
                else:
                    accounts.append(account)
                    bar.update(1)

            begin += 5
            params['begin'] = begin
            time.sleep(interval)
        bar.close()
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

    def search_article(self, keyword, limit=0, interval=3):
        """
        根据关键词搜索原创文章
        :param keyword: 包含关键词的标题
        :param limit:设置获取多少篇文章
        :type interval: int 请求时间间隔，秒
        :return:文章列表
        """

        headers = {
            'Host': 'mp.weixin.qq.com',
            'Connection': 'keep-alive',
            'Origin': 'https://mp.weixin.qq.com',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': '*/*',
            'Referer': f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=10&share=1&token={self.token}&lang=zh_CN",
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8', }

        search_api = self.api_collections('search', 'search article')
        begin = 0
        count = 20
        post_data = {
            "token": self.token,
            "lang": "zh_CN",
            "f": "json",
            "random": random.randrange(0, 999),
            "url": keyword,
            "allow_reprint": 0,
            "begin": begin,
            "count": count
        }
        response = self.session.post(search_api, data=post_data).json()
        total = response.get("total")
        article_list = []

        if limit == 0:
            logger.info("一共搜到%s篇图文,已设置不限制获取数量", total)
            bar = tqdm(total=total)
            limit = total
        else:
            logger.info("一共搜到%s篇图文,已设置限制获取前%s篇图文", total, limit)
            bar = tqdm(total=limit)

        bar.set_description("进度条")
        reach_limit = False

        while not reach_limit:
            page_result = self._search_article_pages(search_api, data=post_data, headers=headers)
            if not page_result:
                reach_limit = True
            for article in page_result:
                if len(article_list) >= limit or len(article_list) > total:
                    reach_limit = True
                else:
                    article_list.append(article)
                    bar.update(1)

            begin += 20
            post_data['begin'] = begin
            time.sleep(interval)
        bar.close()

        return ArticleSearchResult([ArticleWithContent(article) for article in article_list], type=0)

    def _search_article_pages(self, api, data, headers):
        """
        根据页数不断地进行请求

        :param api: 请求的API
        :param data: 包含起始的数据
        :return: 图文字典列表
        """
        article_list = []

        response = self.session.post(api, data=data, headers=headers).json()

        if response['base_resp']['ret'] == 0:
            articles = response.get('list')
            article_list += articles

        return article_list

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
            'begin': 0,
            'count': 20,
            'keyword': '',
            'f': 'json',
            'ajax': 1
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
