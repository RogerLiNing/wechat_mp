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
            },
            'user_analysis': {
                'get analysis':'/misc/useranalysis?&begin_date={0}&end_date={1}&source={2}&token={3}&lang=zh_CN&f=json&ajax=1',
                'get property': '/misc/useranalysis?action=attr&begin_date={0}&end_date={1}&token={2}&lang=zh_CN'
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

        account_info = {
            "create_time": int(time.time()),
            "session": self.session,
            "email": self.email,
            "password": self.password,
            "token": self.token
        }
        self.accounts.update({self.email: account_info})
        with open(filename, 'wb') as f:
            pickle.dump(self.accounts, f)

    def _load_accounts(self, filename="./sessions.pkl"):
        """从pkl文件中加载所有账号信息, 数据格式参考response/accounts.json"""
        if not os.path.exists(filename):
            return {}

        with open(filename, 'rb') as f:
            return pickle.load(f, encoding='utf-8')

    def _load_session(self):
        """反序列化session"""
        # 检查accounts里有没有 对应的账号
        account = self.accounts.get(self.email)
        if account:
            if self._get_token(account.get("session")):
                return account
            else:
                print("登录状态已失效.")
                self._delete_session()
        return None

    def _delete_session(self):
        """
        用于删除过期的session,
        如果在搜索公众号或者文章中 返回的响应 invalid session
        :return:
        """
        del self.accounts[self.email]

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

    
    def get_user_analysis(self, start_date, end_date, source=99999999):
        """
        获取用户分析数据

        :param start_date: 开始日期 格式2020-02-25
        :param end_date: 截止日期 格式2020-02-25
        :param source: 渠道值
        全部渠道：99999999
        搜一搜：1
        扫描二维码：30
        图文页右上角菜单：43
        图文页内公众号名称：57
        名片分享：17
        支付后关注：51
        其他合计：0
        :return:
        """
        headers = {
            'Host': 'mp.weixin.qq.com',
            'Connection': 'keep-alive',
            'Origin': 'https://mp.weixin.qq.com',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': '*/*',
            'Referer': f"https://mp.weixin.qq.com/misc/useranalysis?=&token={self.token}&lang=zh_CN",
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8', }

        api = self.api_collections('user_analysis', 'get analysis').format(start_date,end_date,source,self.token)



        # 先获取所有模板的总数
        response = self.session.get(api, headers=headers)

        data_str = response.json()
        return data_str['category_list'][0]
        # {'user_source': 99999999, 'list': [{'date': '2020-01-01', 'new_user': 0, 'cancel_user': 0, 'netgain_user': 0, 'cumulate_user': 141},

    def get_user_propery(self, start_date, end_date):
        """
        获取用户属性分析数据

        :param start_date: 开始日期 格式2020-02-25
        :param end_date: 截止日期 格式2020-02-25
        :return:
        """
        headers = {
            'Host': 'mp.weixin.qq.com',
            'Connection': 'keep-alive',
            'Origin': 'https://mp.weixin.qq.com',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': '*/*',
            'Referer': f"https://mp.weixin.qq.com/misc/useranalysis?action=attr&token={self.token}&lang=zh_CN",
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8', }

        api = self.api_collections('user_analysis', 'get property').format(start_date,end_date,self.token)


        # 先获取所有模板的总数
        response = self.session.get(api, headers=headers)

        data_str = response.text
        p = re.compile(r'window.cgiData = (\{[\s\S]*\});')
        raw_string = p.findall(data_str)[0]
        p = re.compile(r'\+\("(\d*)"\) \|\| 0')
        p2 = re.compile(r'\s*(.*?): ')
        new_string = ""
        for l in raw_string.split("\n"):
            r = p.findall(l)
            r2 = p2.findall(l)

            if r:
                value = f'"count": {r[0]}'
                value.strip()
                new_string += value

            if r2:
                if "count" not in l:
                    value = f'"{r2[0]}": '
                    new_line = re.sub(r'\s*(.*?): ', value, l)
                    new_string += new_line
            else:
                new_string += l

        new_string = new_string.replace(' || "未知"',"")
        new_string = re.sub(r'\s*',"", new_string)
        new_string = new_string.replace(",]","]")
        json_data = json.loads(new_string)
        for k,v in json_data["list"][0].items():
            print(k,v)
