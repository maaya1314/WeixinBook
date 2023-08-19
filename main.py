#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import json
import pprint
import random
import re
import sys
import os
import time

import requests

import urllib3

from WeReadScan import WeRead

sys.path.append('../..')
sys.path.append('../../..')
sys.path.append('../../../..')
from libs.base import TaskBase
from libs.loghandler import getLogger
from lxml.html import etree

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

urllib3.disable_warnings()


TIME_SLEEP = 1


class WeiXinBook(TaskBase):
    def __init__(self, debug=False):
        TaskBase.__init__(self)
        self.log = getLogger(self.__class__.__name__, console_out=True, level="debug")
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
        }
        self.counts = 0
        self.debug = debug
        self.keyword = ""
        self.exit_flag = False
        self.exit_counts = 0
        self.proxy_flag = False
        self.collection_name = "not_input"
        self.key_field = 'book_id'
        self.max_retry_counts = 3

    def run(self):
        self.headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json;charset=UTF-8',
            'Pragma': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.83 Safari/537.36',
            # 'X-Requested-With': 'XMLHttpRequest',
            'X-Auth': 'b1c394a961a818b00479b22845f31974'
        }
        TIMEOUT = 60

        opt = Options()
        # proxy_http = proxy.get('http')
        # print('--proxy-server=%s' % proxy_http)
        # opt.add_argument('--proxy-server=%s' % proxy_http)  # 添加代理

        # 以最高权限运行
        opt.add_argument('--no-sandbox')
        # 禁用浏览器提示正在受自动化软件控制
        opt.add_experimental_option('useAutomationExtension', False)
        # 防止反爬
        opt.add_experimental_option('excludeSwitches', ['enable-automation'])
        # 添加UA
        opt.add_argument('user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/99.0.4844.83 Safari/537.36"')
        opt.add_argument("--headless")
        opt.add_argument("--disbale-gpu")
        browser = webdriver.Chrome(chrome_options=opt)
        browser.get("https://weread.qq.com/#search")
        browser.implicitly_wait(10)

        # 书籍爬取浏览器，无头selenium
        chrome_options = webdriver.ChromeOptions()
        # now you can choose headless or not
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument('disable-infobars')
        chrome_options.add_argument('log-level=3')
        # launch Webdriver
        print('Webdriver launching...')
        book_driver = webdriver.Chrome(options=chrome_options)
        print('Webdriver launched.')
        with WeRead(book_driver) as weread:
            weread.login()  # ? login for grab the whole book

        index = 0
        while index < 520:
            url = "https://weread.qq.com/web/bookListInCategory/100000?maxIndex={}"
            url = url.format(index)
            content = self.req(url, req_type="get", rsp_type="json", headers=self.headers, timeout=TIMEOUT)
            if not content:
                browser.quit()
                return
            book_list = content['books']
            for book in book_list:
                is_download = 1
                title = book['bookInfo']['title']
                search_input = browser.find_elements(By.XPATH, '//div[@class="search_input_textContainer"]/input')
                search_input[0].clear()
                time.sleep(TIME_SLEEP)
                search_input[0].send_keys(title)
                time.sleep(TIME_SLEEP)
                click = browser.find_elements(By.XPATH, '//span[@class="search_input_right"]')
                click[0].click()
                time.sleep(TIME_SLEEP)
                first_mate = browser.find_element(By.XPATH, '//div[@class="search_result_global"]//li[1]/a')
                link = first_mate.get_attribute('href')
                encryption_id = link.split('/')[-1]
                retry_counts = 0
                while retry_counts < self.max_retry_counts:
                    retry_counts += 1
                    try:
                        book_url = 'https://weread.qq.com/web/reader/{}?'.format(encryption_id)
                        while True:
                            _flag = weread.scan2html(book_url, save_at="./static/books", show_output=False)
                            if not _flag:
                                break
                        is_download = 1
                        break
                    except TimeoutError as e:
                        self.log.error(e)
                        if retry_counts > self.max_retry_counts / 2:
                            time.sleep(10)
                            continue
                    except Exception as e:
                        self.log.error(e)
                        is_download = 0
                        # time.sleep(5)
                # 将book索引强制归0，保证下本书正常获取
                weread.big_book_sort = 0
                data = {
                    "book_id": encryption_id,
                    "book_name": title,
                    "is_download": is_download
                }
                self.upload(data)

                time.sleep(TIME_SLEEP)
            index += 20
        browser.quit()
        print("complete!")


if __name__ == '__main__':
    params = {
        "proxy_flag": False,
        # "proxy_flag": True,
        "query_time": "",
        # "time_sleep": (2, 5)
    }
    obj = WeiXinBook(debug=False)
    obj.process_item(params)
    # obj.run()