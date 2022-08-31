# tang_ying
tangying后端


## Installation

### 安装Python3

1. 下载安装包
    > wget https://www.python.org/ftp/python/3.9.8/Python-3.9.8.tar.xz

2. 安装依赖
    >yum -y install zlib-devel bzip2-devel openssl-devel sqlite-devel gcc make

3. 编译安装

    修改安装配置/Module/Setup文件加载ssl模块，去掉以下注释
    ```python
    # Socket module helper for socket(2)
    _socket socketmodule.c

    # Socket module helper for SSL support; you must comment out the other
    # socket line above, and possibly edit the SSL variable:
    SSL=/usr/local/ssl
    _ssl _ssl.c \
            -DUSE_SSL -I$(SSL)/include -I$(SSL)/include/openssl \
            -L$(SSL)/lib -lssl -lcrypto
    ```
    >./configure <br>
    make && make install

### 创建python3虚拟环境

1. 新建文件夹 
    >makedir py3env

2. 下载python工具包virtualenv(用python3的pip)
    >pip3 install virtualenv

3. 创建python虚拟环境(切换到py3env同级目录)
    >python3 -m virtualenv py3env

4. 切换到虚拟环境
    >source py3env/bin/activate

### 安装django(4.0.6),uwsgi

>pip install django==4.0.6 uwsgi -i http://pypi.douban.com/simple --trusted-host pypi.douban.com


