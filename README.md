# wechat_mp 是什么？
是用来登陆微信公众号后台的第三方库，而登陆后台不是微信操作后台发送群发或者消息等，因为微信本身就提供了开发者文档供用户调用。
微信后台有一些功能是API不提供的，例如以下三个：
- 根据公众号名称搜索公众号，并查看其群发过的图文
- 根据关键词搜索相关的群发图文
- 导出公众号选择的模板行业库中的所有模板示例

# Python版本
- Python 3.6.x

# 初始化项目
```
$ pipenv update
```

# 使用方法
```python
>>> # 根据公众号名搜索其历史群发，并导出到Excel中
>>> from wechat_mp import Wechat
>>> client = Wechat(email=EMAIL, password=PASSWORD, qrcode_console=False)
二维码已打开，请进行扫码 ...
已扫描二维码,等待确认中 ...
已确认登陆 ...
>>> searched_accounts = client.search_official_account(nickname="人民日报")
>>> searched_accounts
[ <OfficialAccount: 人民日报>, <OfficialAccount: 人民日报评论>,<OfficialAccount: 人民日报社>...]
>>> rmrb = searched_accounts[0]
>>> rmrb.total_articles
10435
>>> rmrb.nickname
人民日报
>>> rmrb.alias
rmrbwx
>>> rmrb.round_head_img
http://mmbiz.qpic.cn/mmbiz/xrFYciaHL08CANmCkReiaffGxwG3icrCyoiauzgyuID7YH0XFRenmafvsWDmakLhj86KKiceO275nVzNiafRpotDLdicA/0?wx_fmt=png
>>> rmrb.service_type
0
>>> rmrb.save_as_excel(filename="人民日报图文列表")

```