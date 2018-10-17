# coding:utf-8

"""
    @author  : linkin
    @email   : yooleak@outlook.com
    @date    : 2018-10-04
"""

import time
import math
import gevent
import requests
import logging
from gevent                 import pool
from gevent                 import monkey
from config.DBsettings      import _DB_SETTINGS
from config.DBsettings      import _TABLE
from config.config          import CONCURRENCY
from config.config          import VALIDATE_AMOUNT
from config.config          import VALIDATE_F
from const.settings         import mul_validate_url
from const.settings         import v_headers
from config.config          import VALIDATE_RETRY
from components.rator       import Rator
from components.dbhelper    import Database
from requests.adapters      import HTTPAdapter
from tools.util             import find_proxy
from tools.util             import get_proxy

monkey.patch_socket()
logger = logging.getLogger('Validator')

class Validator(object):
    def __init__(self):
        self.db         = Database(_DB_SETTINGS)
        self.db.table   =  _TABLE['standby']
        self.rator      = Rator(self.db)

    def check_allot(self,proxies):
        p_len = len(proxies)
        offset = 10
        params_dict = []
        if p_len<=offset:
            return ['&'.join(['ip_ports%5B%5D={}%3A{}'.format(i.split(':')[0],i.split(':')[1])
                             for i in proxies ])]
        else:
            base = math.ceil(p_len/offset)
            p_groups = [proxies[i*offset:(i+1)*offset] for i in range(base)]
            for group in p_groups:
                url_str = '&'.join(['ip_ports%5B%5D={}%3A{}'.format(i.split(':')[0],i.split(':')[1])
                             for i in group])
                params_dict.append(url_str)
            return params_dict

    def run(self, proxyList):
        logger.info('Running Validator.')
        self.rator.begin()
        while 1:
            try:
                if proxyList:
                    self.rator.pull_table(self.db.table)
                    pen = len(proxyList)
                    logger.info('Proxies from Collector is detected,length : %d '%pen)
                    pop_len =  pen if pen <= VALIDATE_AMOUNT else VALIDATE_AMOUNT
                    stanby_proxies =[proxyList.pop() for x in range(pop_len)]
                    prams_dict = self.check_allot(stanby_proxies)
                    logger.info('Start to verify the collected proxy data,amount: %d '%pop_len)
                    gpool = pool.Pool(CONCURRENCY)
                    gevent.joinall([gpool.spawn(self.validate_proxy,i) for i in prams_dict])
                    logger.info('Validation finished.Left collected proxies:%d'%len(proxyList))
                    time.sleep(VALIDATE_F)
            except Exception as e:
                logger.error('Error class : %s , msg : %s '%(e.__class__,e))
                self.rator.end()
                logger.info('Validator shuts down.')
                return

    def validate_proxy(self,url_str):
        _proxies = {}
        session = requests.Session()
        session.mount('http://', HTTPAdapter(max_retries=VALIDATE_RETRY))
        session.mount('https://', HTTPAdapter(max_retries=VALIDATE_RETRY))
        while 1:
            try:
                response = session.get(mul_validate_url+url_str,
                                        proxies = _proxies,
                                        headers=v_headers,
                                        timeout=20)
                data = response.json()
            except Exception as e:
                    _proxies = get_proxy()
                    continue
            else:
                for res in data['msg']:
                    if 'anony' in res and 'time' in res:
                        ip, port = res['ip'],res['port']
                        bullet = {'ip':ip,'port':port,'anony_type':res['anony'],
                                  'address':'','score':0,'valid_time':'',
                                  'resp_time':res['time'],'test_count':0,
                                  'fail_count':0,'createdTime':'','combo_success':1,'combo_fail':0,
                                  'success_rate':'','stability':0.00}
                        self.rator.mark_success(bullet)
                return
