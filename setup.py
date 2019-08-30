import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="wechat-mp",
    version="1.2.0",
    author="Roger Lee",
    author_email="704482843@qq.com",
    description="导出一个公众号里的所有群发图文、根据关键词搜索原创图文和导出行业模板消息示例",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RogerLiNing/wechat_mp",
    packages=setuptools.find_packages(),
    install_requires=[
        "requests",
        "pillow",
        "openpyxl",
        "beautifulsoup4",
        "threadpool",
        "tqdm",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
