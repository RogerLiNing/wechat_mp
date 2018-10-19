# wechat_mp 是什么？
是用来登陆微信公众号后台的第三方库，而登陆后台不是微信操作后台发送群发或者消息等，因为微信本身就提供了开发者文档供用户调用。
微信后台有一些功能是API不提供的，例如以下三个：
- [x] 根据公众号名称搜索公众号，并查看其群发过的图文
- [ ] 根据关键词搜索相关的群发图文
- [x] 导出公众号选择的模板行业库中的所有模板示例

# Python版本
- Python 3.6.x
- 如果是3.7，需要你去Pipfile文件中，将python_version改成3.7。

# 初始化项目
```
$ git clone https://github.com/RogerLiNing/wechat_mp.git
$ cd wechat_mp
$ pip3 install pipenv
$ pipenv update
$ pipenv shell
$ ipython
```
# 如果pipenv update有问题
```
$ pipenv shell
$ pip install -r requirements.txt
```

# 使用方法
### 1. 查询某个公众号的历史群发图文
##### 目前支持：
- 根据名称搜索公众号
- 公众号本身是对象，可以通过对象方法articles获取其图文列表
- 图文本身也是对象，可以查看其属性
- 可以将图文列表导出到Excel文件中

##### 请看实际例子
```python
>>> # 根据公众号名搜索其历史群发，并导出到Excel中
>>> from wechat_mp import Wechat
>>> client = Wechat(email=EMAIL, password=PASSWORD)
开始模拟登陆 账号 xxxxxxxxxxx
跳转二维码扫码页面                
已经获取二维码图片并显示，等待扫码        
开始检查二维码是否被扫和是否已确认        
尚未扫码                     
尚未扫码                     
尚未扫码                     
尚未扫码                     
已经扫码了，等待确认               
已完成扫码，开始post登陆到微信后台的请求   
Post登陆成功                 
保存登陆cookies,避免重复登陆       
获取token：145035170        
>>> accounts = client.search_account("编程这件事儿",limit=6)
一共有73个公众号,限制获取6个公众号
正在获取第0到第5个
正在获取第5到第10个
正在获取第10到第15个
>>> accounts
[<OfficalAccount: 编程这件事儿>,
 <OfficalAccount: 编程这件小事>,
 <OfficalAccount: 可爱这件事儿>,
 <OfficalAccount: 人生这件事儿>,
 <OfficalAccount: 护肤这件事儿>,
 <OfficalAccount: 生活这件事儿>,
 <OfficalAccount: 设计这件事儿>]
>>> my_account = accounts[0]
>>> my_account
<OfficalAccount: 编程这件事儿>
>>> articles = my_account.articles()
一共6篇文章，已设置获取个数:None
>>> articles
[<Article: 教你如何使用ngrok内网穿透让外网可以访问你本地的Django网站>,
 <Article: [推荐]三款可以在安卓手机上运行Python代码的软件>,
 <Article: 针对Python初学者的11个小贴士>,
 <Article: Python字符串格式化的四种姿势>,
 <Article: Steam新型盗号木马及产业链分析报告>,
 <Article: [教程]如何使用Python3导出MySQL数据库字典>]
>>> first_article = articles[0]
>>>  first_article
<Article: 教你如何使用ngrok内网穿透让外网可以访问你本地的Django网站>
>>>   first_article.title
'当你在本地开发一个网站的时候，你想要发给别人进行访问，但是又不想放到服务器上面（毕竟上传也是挺麻烦的）
。'
>>> first_article.update_time
'2018-08-02 23:49:57'    
>>> first_article.link
'http://mp.weixin.qq.com/s?__biz=MzU1MzEyMzYxMA==&mid=2247483679&idx=1&sn=b36c581c3639a7da40427adc88a7140f&chksm=fbf6eb6acc81627c2f697d70e16573b4f139616b6be323781d387fa457b592a12ae09fff20e4#rd'
>>> my_account.save_articles_as_excel("编程这件事儿")
```
![文件内容](https://user-images.githubusercontent.com/18111035/45262013-47c80e80-b440-11e8-86df-12ad6c6ab787.png)

### 3. 导出公众号选择的模板行业库中的所有模板示例
##### 目前支持：
- 获取公众号目前的模板行业里的所有模板
- 可以获取具体示例
##### 目前不支持
- 导出到excel文件

##### 使用方法
```python
>>> templates = client.get_templates(threads=20, detail=True) # threads是使用多少个线程跑，detail是否获取具体示例
>>> templates[0] # 查看第一个模板

{'class1': 'IT科技',
 'class2': '互联网|电子商务',
 'id': 'OPENTM228356100',
 'person_used': 46,
 'title': '创建简历成功提醒',
 'detail': {'class1': 'IT科技',
  'class2': '互联网|电子商务',
  'content': '{{first.DATA}}\n简历名称：{{keyword1.DATA}}\n发布时间：{{keyword2.DATA}}\n{{remark.DATA}}',
  'example': '您在58同城上创建简历成功\r\n简历名称：财务主管\r\n发布时间：2014-07-27\r\n若非本人操作请联系客服中心进行修改',
  'id': 'OPENTM228356100',
  'modify_time': '2015-01-15 16:47:52',
  'person_used': 46,
  'title': '创建简历成功提醒'}}

```

# 作者公众号
### 编程这件事儿
![编程这件事儿](https://mp.weixin.qq.com/mp/qrcode?scene=10000004&size=102&__biz=MzU1MzEyMzYxMA==&mid=2247483679&idx=1&sn=b36c581c3639a7da40427adc88a7140f&send_time=)
