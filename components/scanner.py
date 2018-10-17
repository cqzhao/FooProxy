#coding:utf-8

"""
    @author  : linkin
    @email   : yooleak@outlook.com
    @date    : 2018-10-08
"""

import time
import json
import math
import logging
import aiohttp
import asyncio
from config.DBsettings      import _DB_SETTINGS
from config.DBsettings      import _TABLE
from config.config          import COROUTINE_MAX
from config.config          import LOCAL_AMOUNT
from config.config          import VALIDATE_LOCAL
from const.settings         import mul_validate_url
from const.settings         import v_headers
from components.rator       import Rator
from components.dbhelper    import Database
from tools.util             import find_proxy

logger = logging.getLogger('Scanner')

class Scaner(object):
    def __init__(self):
        self.db = Database(_DB_SETTINGS)
        self.db.table = _TABLE['standby']
        self.rator = Rator(self.db)
        self.standby_data = []

    def check_allot(self,proxies):
        p_len = len(proxies)
        offset = 20
        params_dict = {}
        if p_len<=offset:
            return {'&'.join(['ip_ports%5B%5D={}%3A{}'.format(i['ip'],i['port'])
                             for i in proxies]):proxies}
        else:
            base = math.ceil(p_len/offset)
            p_groups = [proxies[i*offset:(i+1)*offset] for i in range(base)]
            for group in p_groups:
                url_str = '&'.join(['ip_ports%5B%5D={}%3A{}'.format(i['ip'],i['port'])
                             for i in group])
                params_dict[url_str] = group
            return params_dict

    def run(self):
        logger.info('Running Scanner.')
        self.rator.begin()
        loop = asyncio.get_event_loop()
        while 1:
            try:
                if self.standby_data :
                    pen = len(self.standby_data )
                    logger.info('Start the validation of the local "standby" database,length : %d ' % pen)
                    pop_len = pen if pen <= LOCAL_AMOUNT else LOCAL_AMOUNT
                    stanby_proxies = [self.standby_data.pop() for x in range(pop_len)]
                    prams_dict = self.check_allot(stanby_proxies)
                    semaphore = asyncio.Semaphore(COROUTINE_MAX)
                    logger.info('Start to verify the standby proxy data,amount: %d ' % pop_len)
                    tasks = [asyncio.ensure_future(self.validate(i,prams_dict[i],semaphore)) for i in prams_dict]
                    loop.run_until_complete(asyncio.gather(*tasks))
                    logger.info('Local validation finished.Left standby proxies:%d' % len(self.standby_data ))
                    time.sleep(VALIDATE_LOCAL)
                else:
                    self.standby_data = self.db.all()
            except Exception as e:
                logger.error('Error class : %s , msg : %s ' % (e.__class__, e))
                self.rator.end()
                loop.close()
                logger.info('Scanner shuts down.')
                return

    async def validate(self,url_str, proxies,semaphore):
        # 可设置响应超时对API服务器请求代理，没写
        async with semaphore:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(mul_validate_url+url_str,
                                   headers=v_headers) as response:
                        data = await response.text(encoding='utf-8')
                        data = json.loads(data)
                except Exception as e:
                    logger.error('Error class : %s , msg : %s ' % (e.__class__, e))
                    return
                else:
                    for res in data['msg']:
                        proxy = find_proxy(res['ip'],res['port'],proxies)
                        if 'anony' in res and 'time' in res:
                            proxy['anony_type'] = res['anony']
                            proxy['resp_time'] = res['time']
                            self.rator.mark_update(proxy, collected=False)
                        else:
                            self.rator.mark_fail(proxy)
