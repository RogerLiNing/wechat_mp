# wechat_mp 是什么？
是用来登陆微信公众号后台的第三方库，而登陆后台不是微信操作后台发送群发或者消息等，因为微信本身就提供了开发者文档供用户调用。
微信后台有一些功能是API不提供的，例如以下三个：
- [x] 根据公众号名称搜索公众号，并查看其群发过的图文
- [x] 根据关键词搜索相关的群发图文
- [x] 导出公众号选择的模板行业库中的所有模板示例

# Python版本
- Python 3.6.x



# 如何安装

## 源码安装

```
$ git clone https://github.com/RogerLiNing/wechat_mp.git
$ cd wechat_mp
$ python setup.py install
```

## pip 安装

```shell
pip install wechat-mp
```



# 使用方法

## 登陆
需要注意，你需要先[注册](https://mp.weixin.qq.com/cgi-bin/registermidpage?action=index&lang=zh_CN&token=)一个微信公众号账号，
服务号或者订阅号都可以。需要注意，只有认证的服务号才能获取行业模板消息。
enable_cookies参数控制是否保持登录, 默认为False，

需要注意的是，目前使用PIL弹出二维码，如果在没有GUI的操作系统无法扫码。

当同一账号连续输错三次密码时，会需要输入验证码，届时会自动打开验证码图片，记住验证码后关闭图片查看，然后在程序中输入验证码即可。

```python
from wechat_mp import WeChat

EMAIL = "me@example.com"
PASSWORD = "admin"

# 可同时初始化多个不同的账号，例如client1, client2
client = WeChat(email=EMAIL, password=PASSWORD, enable_cookies=True)
```



## 1. 查询某个公众号的历史群发图文

目前支持：
- 根据名称搜索公众号
- 公众号本身是对象，可以通过对象方法articles获取其图文列表
- 图文本身也是对象，可以查看其属性
- 可以将图文列表导出到Excel文件中

### 搜索公众号：
返回公众号对象列表，公众号对象中主要的两个：nickname 和 service_type
```python
accounts = client.search_account("python阅读空间", limit=10)
```
### 公号对象属性
| 属性           | 解释       |
| -------------- | ---------- |
| fakeid         | ID         |
| nickname       | 公众号昵称 |
| alias          | 自定义昵称 |
| round_head_img | 圆头像地址 |
| service_type   | 公号类型   |


### 获取公众号的推送图文
这里选取了第一个账号，调用`articles()`方法获取其所有的图文。有些公众号有很多图文，传入`limit`参数来获取前N篇图文。
你也可以传入`title_contain`参数来只获取标题包含特定关键词的图文，可以传入`interval`参数来限制请求频率，默认3秒。

```python
articles = accounts[0].articles()
```
### 图文对象属性
| 属性     | 解释             |
| -------- | ---------------- |
| aid      | 群发ID+ 群发序号 |
| appmsgid | 群发id           |
| cover    | 封面地址         |
| digest   | 图文摘要         |
| itemidx  | 图文群发序号     |
| link     | 图文链接         |
| title    | 图文标题         |


### 导出到文件
调用图文结果对象`articles` 提供了 `save_articles_as_excel`方法可以导出图文结果到Excel文件。
```python
articles.save_articles_as_excel("python阅读空间")
```


## 2.根据关键词搜索图文

目前支持：
- 根据关键词搜索图文
- 图文本身也是对象，可以查看其属性
- 可以将图文列表导出到Excel文件中

### 搜索图文
调用`search_article`方法会返回一个结果对象，你可以是用`for`循环输出打印
```python
result = client.search_article("python内存管理",limit=100)
```
### 图文对象属性
| 属性                  |                          |
| --------------------- | ------------------------ |
| article_type          | 图文类目                 |
| author                | 作者                     |
| content               | 正文内容（包含HTML代码） |
| cover_url             | 封面地址                 |
| head_img_url          | 公众号头像地址           |
| nickname              | 公众号昵称               |
| source_can_reward     |                          |
| source_reprint_status |                          |
| source_url            |                          |
| title                 | 图文标题                 |
| url                   | 图文地址                 |

### 将图文导出到Excel文件

调用图文结果对象`result` 提供了 `save_articles_as_excel`方法可以导出图文结果到Excel文件。

```python
result.save_articles_as_excel("python内存管理")
```



# 作者公众号

### Python阅读空间
![Python阅读空间](https://mp.weixin.qq.com/mp/qrcode?scene=10000004&size=102&__biz=MzU1MzEyMzYxMA==&mid=2247483679&idx=1&sn=b36c581c3639a7da40427adc88a7140f&send_time=)

## 打包
``` 
python -m pip install --user --upgrade setuptools wheel
python setup.py sdist bdist_wheel

dist/
  example_pkg_your_username-0.0.1-py3-none-any.whl
  example_pkg_your_username-0.0.1.tar.gz
```
## 上传
``` 
python -m pip install --user --upgrade twine
python -m twine upload dist/*
```



## 作者

- [Roger Lee](<https://github.com/RogerLiNing>)



## 贡献者

- [Zheng](<https://github.com/zxyle>)
