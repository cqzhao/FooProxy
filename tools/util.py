#coding:utf-8
"""
    @author  : linkin
    @email   : yooleak@outlook.com
    @date    : 2018-10-04
"""
import re
import time
import json
import base64
import hashlib
import requests
from const.settings import IP_check_url
from const.settings import IP_check_url_01
from const.settings import IP_check_url_02
from const.settings import IP_check_url_03
from const.settings import headers
from const.settings import proxy_api
from bs4            import BeautifulSoup as bs

def time_to_date(timestamp):
    """
    时间戳转换为日期
    :param timestamp : 时间戳，int类型，如：1537535021
    :return:转换结果日期，格式： 年-月-日 时:分:秒
    """
    timearr = time.localtime(timestamp)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timearr)
    return  otherStyleTime

def get_ip_addr(ip):
    """
    获取ip的地址信息
    :param ip : IP地址
    :return: 地址信息
    """
    try:
        resp = requests.get(IP_check_url+ip,headers=headers)
        rep = bs(resp.text,'lxml')
        try:
            res = rep('code')[1].text
        except Exception as e:
            return 'unknown'
        return res
    except Exception as e:
        return 'unknown'

def get_ip_addr_01(ip):
    """
        获取ip的地址信息
        :param ip : IP地址
        :return: 地址信息
        """
    try:
        resp = requests.get(IP_check_url_01 + ip, headers=headers)
        try:
            res = resp.json()
            data = res['data']
            country = data['country'] if data['country']!='XX' else ''
            city    = data['city'] if data['city']!='XX' else ''
            region  = data['region'] if data['region']!='XX' else ''
            isp     = data['isp'] if data['isp']!='XX' else ''
            addr = country+region+city+isp
        except Exception as e:
            return 'unknown'
        else:
            return addr
    except Exception as e:
        return 'unknown'

def get_ip_addr_02(ip):
    """
        获取ip的地址信息
        :param ip : IP地址
        :return: 地址信息
        """
    try:
        resp = requests.post(IP_check_url_02,data={'ip':ip}, headers=headers)
        try:
            res = resp.json()
            data = res['text']
            addr = data['ipip_location']
        except Exception as e:
            return 'unknown'
        else:
            return addr
    except Exception as e:
        return 'unknown'

def get_ip_addr_03(ip):
    """
    获取ip的地址信息
    :param ip : IP地址
    :return: 地址信息
    """
    try:
        resp = requests.get(IP_check_url_03+ip, headers=headers)
        try:
            res = resp.text.strip()
        except Exception as e:
            return 'unknown'
        else:
            return res
    except Exception as e:
        return 'unknown'

def get_cookies(url, headers=headers, params={},proxies={}):
    """
    异步获取某个url的cookie并返回
    :param url: 要获取cookie的网址
    :param headers: 给定的请求头部
    :param params: 请求参数
    :return: 需要的cookies
    """
    cookies = requests.get(url, headers=headers, params=params,proxies=proxies).cookies
    return cookies

def get_nyloner_params(page,num):
    """
    获取代理ip提供网站:https://www.nyloner.cn的请求伪造参数
    :param page: 请求页面所在页数 (一般设为1，后续num设定爬取多少条ip便可)
    :param num: 这一页要爬取的代理ip条数
    :return: 有效的请求伪造参数
    """
    timestamp = int(time.time())
    token = hashlib.md5(str(page).encode(encoding='UTF-8')+
                        str(num).encode(encoding='UTF-8')+
                        str(timestamp).encode(encoding='UTF-8')).hexdigest()
    return {
        'page':page,
        'num':num,
        'token':token,
        't'	: timestamp,
    }

def base64_decode(data,key='\x6e\x79\x6c\x6f\x6e\x65\x72'):
    """
    IP代理网站：https://www.nyloner.cn/proxy的代理抓取json数据解密函数
    :param data: 抓取的json数据的list的加密内容
    :param key : 加密的key 默认为'\x6e\x79\x6c\x6f\x6e\x65\x72'即是'nyloner'
    :return: 返回解密list内容,json格式
    """
    data = base64.b64decode(data)
    code = ''
    for x in range(len(data)):
        j = x % len(key)
        code += chr((data[x]^ord(key[j]))%256)
    decoded_data = str(base64.b64decode(code)).lstrip('b').strip('\'')
    return json.loads(decoded_data)

def  is_proxy_valid(proxy):
    """
    :usage:
    判断给定的代理ip是否符合格式要求:"<ip>:<port>"
    :param data:
    @proxy	: 要判断的代理ip
    :return:
    @result	: 符合要求则返回 代理ip，否则为 []
    """
    return re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b\:\d+',proxy)


def format_proxies(proxy_list):
    """
    :param proxy_list:
    代理ip列表 格式：['<ip>:<port>',..],
    或者单个代理ip，如果未经过格式化，但符合代理ip格式"<ip>:<port>"，即对其格式化后返回
    :return:
    格式化后的代理ip列表  格式：
    [{'http':'http://<ip>:<port>','https':'https://<ip>:<port>'},{},{},..]
    或 格式化后的单个代理IP：
    {'http':'http://<ip>:<port>','https':'https://<ip>:<port>'}
    """
    if not isinstance(proxy_list,list):
        if bool(is_proxy_valid(proxy_list)):
            return {
                'http': 'http://' + proxy_list,
                'https': 'https://' + proxy_list,
            }
        else:
            raise TypeError('Not a valid type of IP proxy.')
    return [
        {
        'http'	:	'http://'	+ i,
        'https'	: 	'https://' 	+ i,
        }
        for i in proxy_list
    ]


def get_proxy(kind='anony'):
    if kind not in ['anony', 'normal']:
        return None
    url = proxy_api.format(kind=kind)
    try:
        res = requests.get(url)
    except Exception as e:
        return {}
    else:
        proxy = res.json()
        if proxy:
            formatted_proxy = format_proxies(':'.join([proxy['ip'], proxy['port']]))
        else:
            return {}
        return formatted_proxy

def find_proxy(ip,port,proxies):
    for i in proxies:
        if i['ip']==ip and i['port']==port:
            return i
    return {}