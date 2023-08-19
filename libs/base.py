#!/usr/bin/env python
# -*- coding:utf-8 -*-
import datetime
import json
import random
import time
from urllib.parse import urlparse

import pymongo
import requests
import os
import pandas as pd
from openpyxl import load_workbook

import sys

from pymongo import UpdateOne
from pymongo.errors import WriteError
from redis import ConnectionPool, Redis, StrictRedis
from fake_useragent import UserAgent
from urllib3 import encode_multipart_formdata
# from selenium import webdriver
# from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from playwright.sync_api import sync_playwright
# import asyncio
sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
from libs import util
from libs.loghandler import getLogger
logger = getLogger("CssTaskBase", console_out=True, level="debug")
# MAX_RETRY = 10
TIMEOUT = 60
# from sites.common.connectdb import MongoDB, DataCenterDB


# class DataCenterDB(object):
#     MONGODB_SERVER = "127.0.0.1"
#     MONGODB_PORT = 27017
#     authSource = True
#     MONGODB_DB = "data_service"
#     MONGO_USER = ""
#     MONGO_PSW = ""


class DataCenterDB(object):
    MONGODB_SERVER = "101.91.148.86"
    MONGODB_PORT = 6601
    authSource = True
    MONGODB_DB = "data_center"
    MONGO_USER = "work"
    MONGO_PSW = "work"


class MongoDB(object):
    def __init__(self, mongodb):
        if hasattr(mongodb, 'authSource'):
            authSource = 'admin'
        else:
            authSource = mongodb.MONGODB_DB
        mongo_url = 'mongodb://{0}:{1}@{2}:{3}/?authSource={4}&authMechanism=SCRAM-SHA-1'.format(mongodb.MONGO_USER, mongodb.MONGO_PSW, mongodb.MONGODB_SERVER, mongodb.MONGODB_PORT, authSource)
        # mongo_url = 'mongodb://localhost:27017'
        self.client = pymongo.MongoClient(mongo_url)
        # self.client = pymongo.MongoClient(mongodb.MONGODB_SERVER, mongodb.MONGODB_PORT)
        self.db = self.client[mongodb.MONGODB_DB]
        # self.db.authenticate(mongodb.MONGO_USER, mongodb.MONGO_PSW)


        # self.collection = db[mongodb.MONGODB_COLLECTION]

        # 建立索引
        # self.collection.ensure_index([("_utime", pymongo.ASCENDING)])
        # self.collection.ensure_index([("_in_time", pymongo.ASCENDING)])
        # self.collection.ensure_index([("_record_id", pymongo.ASCENDING)])

    def __del__(self):
        self.client.close()

    def find_data(self, value, collection, query_name=None):
        coll = self.db[collection]
        if not query_name:
            query_name = '_id'
        cursor = coll.find({query_name: value}, no_cursor_timeout=True)
        data_list = list(cursor)
        if data_list:
            return True
        return False

    def insert_item(self, collection, value, doc=None):
        coll = self.db[collection]
        _in_time = util.get_now_time()

        # coll.insert({'_id': value})
        if not doc:
            coll.update_one({'_id': value}, {'$set': {'_id': value, '_in_time': _in_time}}, upsert=True)
        else:
            if not isinstance(doc, dict):
                return
            doc['_in_time'] = _in_time
            coll.update_one({'_id': value}, {'$set': doc}, upsert=True)

    def get_company(self, collection, query=None):
        if not query:
            query = {}
        coll = self.db[collection]
        cursor = coll.find(query, no_cursor_timeout=True)
        for doc in cursor:
            keyword = '{}'.format(doc.get('_id'))
            yield keyword

    def get_keyword(self, province, collection):
        coll = self.db[collection]
        cursor = coll.find({}, no_cursor_timeout=True)
        for doc in cursor:
            keyword = '{}{}'.format(province, doc.get('_id'))
            yield keyword

    def insert_items(self, items, collection):
        collection = self.db[collection]
        for item in items:
            if not item:
                continue

            logger.info(item)
            cursor = collection.find({'_record_id': item['_record_id']})
            cursor = list(cursor)
            if cursor:
                if item.get('_in_time'):
                    del item['_in_time']
                collection.update({'_record_id': item['_record_id']}, {'$set': dict(item)}, upsert=True)
            else:
                collection.insert(dict(item))

    def insert_batch_data(self, collection, data_list, update_item=None, is_order=False, insert=False):
        count = 0
        if data_list is None:
            return count

        length = len(data_list)
        if length <= 0:
            return count

        try:
            bulk = self.db[collection].initialize_ordered_bulk_op() if is_order else self.db[collection].initialize_unordered_bulk_op()
            for item in data_list:
                if update_item:
                    item = update_item
                if insert:
                    bulk.insert(item)
                else:
                    _id = item.get('_id')
                    bulk.find({'_id': _id}).upsert().update({'$set': item})
                count += 1
            bulk.execute({'w': 0})
            if not update_item:
                logger.info('insert_logs: {length}'.format(length=len(data_list)))
        except WriteError as e:
            logger.error('mongo写入异常:')
            logger.exception(e)
            sys.exit(1)
        except Exception as e:
            logger.error("mongo操作异常: ")
            logger.exception(e)
            raise e
        return count


class RedisConf(object):
    host = "125.88.221.92"
    port = 6379
    db = 1
    password = "yongli@123"
    name = "yny_proxies_list"


class Proxies(object):
    def __init__(self):  #
        self.redis_conn = StrictRedis(host=RedisConf.host, port=RedisConf.port, db=RedisConf.db, password=RedisConf.password)
        # self.redis_pool = ConnectionPool(host=RedisConf.host, port=RedisConf.port, password=RedisConf.password, db=RedisConf.db)
        # self.redis_conn = Redis(connection_pool=self.redis_pool)
        self.redis_name = RedisConf.name

    def get_proxy(self):
        while 1:
            proxy_lens = self.redis_conn.llen(self.redis_name)
            proxy_index = random.choice(range(proxy_lens))
            proxy = self.redis_conn.lindex(self.redis_name, proxy_index)
            proxy = json.loads(proxy)
            if not proxy:
                time.sleep(0.01)
                continue
            break
        # log.info(f">>> 线程获取： {getcurrentname()} : {proxy}")

        return proxy


class TaskBase(object):
    def __init__(self):
        self.debug = False
        self.log = getLogger(self.__class__.__name__, console_out=True, level="debug")
        self.proxy_flag = False
        self.max_pages = 1
        self.max_retries = 10
        self.columns_list = []
        self.counts = 0
        self.collection_name = ""
        self.key_field = ""
        self.db = ""
        self.ua = UserAgent
        self.user_agent_list = [
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
            "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
            "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"]
        self.headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json;charset=UTF-8',
            'Pragma': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.83 Safari/537.36',
        }
        self.items_list = []
        self.partition_key_list = []
        self.rcm_id = ""

    def __call__(self, *args, **kwargs):
        dt = time.time()
        self.log.info("start: {}".format(self.__class__.__name__))
        self._init_work()
        self.start(*args, **kwargs)
        self.log.info("end at {} s".format(str(time.time() - dt)))

    def _init_work(self):
        pass

    def run(self):
        pass

    def get_proxy(self, proxy_type="xxdl"):
        if proxy_type=="ipidea":
            return self.get_ipidea()
        elif proxy_type=="xxdl":
            return self.get_xxdl()
        return self.get_xxdl()

    def get_xxdl(self):
        max_retry = 5
        retry_counts = 0
        proxy_dict = {}
        while retry_counts < max_retry:
            retry_counts += 1
            time.sleep(0.01)
            try:
                p = Proxies()
                proxy_dict = p.get_proxy()
            except Exception as e:
                logger.error("get proxies failed {}".format(e))

            return proxy_dict

    def get_ipidea(self):
        max_retry = 5
        retry_counts = 0
        ipidea_url = "http://api.proxy.ipidea.io/getBalanceProxyIp?num=1&return_type=json&lb=1&sb=0&flow=1&regions=&protocol=http"
        while retry_counts < max_retry:
            retry_counts += 1
            time.sleep(0.1)
            resp = requests.get(url=ipidea_url, timeout=5)
            try:
                dataBean = resp.json()
            except ValueError:
                continue
            else:
                code = dataBean["code"]
                if code == 0:
                    for proxy in dataBean["data"]:
                        proxy_dict = {
                            'http': "http://{}:{}".format(proxy["ip"], proxy["port"]),
                            'https': "http://{}:{}".format(proxy["ip"], proxy["port"]),
                        }
                        return proxy_dict

    def start(self, *args, **kwargs):
        raise NotImplemented()

    def req(self, url, simulation=False, req_type="get", rsp_type="text", anti_word="", encoding=True, req_again=False, **kwargs):
        retry_counts = 0
        self.log.debug("start requests: {}".format(url))
        if simulation:
            content = self.req_simulation(url, **kwargs)
            return content
        while retry_counts < self.max_retries:
            # if retry_counts:
            #     time.sleep(TIMEOUT)
            retry_counts += 1
            if not kwargs.get("timeout"):
                kwargs["timeout"] = 20
            if not kwargs.get("verify"):
                kwargs['verify'] = False
            session = requests.session()
            if kwargs.get("headers"):
                try:
                    user_agent = self.ua().random
                except:
                    user_agent = random.choice(self.user_agent_list)
                finally:
                    kwargs["headers"]["User-Agent"] = user_agent
            if self.proxy_flag:
                proxies = self.get_proxy()
                kwargs["proxies"] = proxies
                # session.proxies = proxies
            try:
                if req_type == "get":
                    response = session.get(url, **kwargs)
                elif req_type == "post":
                    response = session.post(url, **kwargs)
                elif req_type == 'put':
                    response = session.put(url, **kwargs)
                else:
                    self.log.error("error req_type: {}".format(req_type))
                    continue
                if req_again:
                    cookies = response.cookies
                    self.cookies = ''
                    for k, v in cookies.items():
                        self.cookies += "{}={};".format(k, v)
                    kwargs['headers']['cookie'] = self.cookies
                    if req_type == "get":
                        response = session.get(url, **kwargs)
                    elif req_type == "post":
                        response = session.post(url, **kwargs)
                    kwargs['headers'].pop('cookie')
                if not response or response.status_code not in (200, 302, 201, 204):
                    if response.status_code in (400, 404):
                        return response.status_code, response.text
                    if retry_counts > self.max_retries / 2:
                        self.log.error("error response, {}, {}, url:{}".format(response.status_code, retry_counts, url))
                        # time.sleep(10)
                        # self.get_cookies()
                        # self.headers['cookie'] = self.cookie
                        # kwargs["headers"]['cookie'] = self.cookie
                    continue
                if encoding:
                    # response.encoding = 'utf8'
                    response.encoding = response.apparent_encoding
                if not rsp_type or rsp_type == "text":
                    content = response.text
                elif rsp_type == "content":
                    content = response.content
                elif rsp_type == "json":
                    content = response.json()
                elif rsp_type == 'res_and_ses':
                    return response, session
                else:
                    self.log.error("error content:{}".format(response.text))
                    continue
                if anti_word and anti_word in content:
                    self.log.error("anti_word: {}".format(anti_word))
                    continue
                # 根据实际情况设置休眠时间
                # time.sleep(random.randint(2, 5))
                return content
            except TimeoutError as e:
                self.log.error(e)
                if retry_counts > self.max_retries / 2:
                    time.sleep(10)
                    # self.get_cookies()
                    # self.headers['cookie'] = self.cookie
                    # kwargs["headers"]['cookie'] = self.cookie
                    continue
            except Exception as e:
                if retry_counts > self.max_retries / 2:
                    self.log.error("retry counts: {}, {}, {}".format(retry_counts, e, url))
                    # time.sleep(TIMEOUT / 10)
                continue

    def req_playwright(self, url):
        with sync_playwright() as p:
            # 驱动浏览器，并开启无头模式
            browser = p.chromium.launch(headless=True)
            # 打开窗口
            page = browser.new_page()
            # 触发 事件
            # page.on('response', on_response)
            # 访问URL
            page.goto(url)
            page.wait_for_load_state('networkidle')
            # 生成器
            # yield page.content()
            content = page.content()
            # Get_the_data(page.content())
            browser.close()
            return content

    def req_simulation(self, url, **kwargs):
        content = self.req_playwright(url)
        return content

    def _init_db(self, db_obj):
        self.db = MongoDB(db_obj)
        indexs = self.db.db[self.collection_name].index_information()
        index_name = "{}_-1".format(self.key_field)
        if index_name not in indexs:
            self.db.db[self.collection_name].create_index([(self.key_field, -1)], unique=True)

    def process_item(self, params):
        self._init_db(DataCenterDB)

        try:
            query_time = int(params.get("query_time"))
        except:
            query_time = 9999
            self.log.info("not query_time value: {}, set query_time:{}".format(params.get('query_time'), query_time))
        cur_time = datetime.datetime.now()
        self.query_time = str((cur_time + datetime.timedelta(days=-query_time)).strftime('%Y-%m-%d'))
        self.proxy_flag = params.get("proxy_flag")
        self.time_sleep = params.get('time_sleep')
        self.run()
        self.check_upload_db()

    def fix_data(self, data):
        new_data = {}
        for k, v in data.items():
            # self.log.debug("{}: {}".format(k, v))
            if isinstance(v, str):
                v = str(v.replace(" ", " ").strip())
            new_data[k] = v
        # update_time = datetime.datetime.now(datetime.timezone.utc).isoformat()  # datetime更新时间
        update_time = datetime.datetime.now().strftime('%Y-%m-%d')
        new_data['update_time'] = update_time
        self.items_list.append(new_data)
        url = data.get(self.key_field)
        # date = datetime.datetime.strptime(publish_time.split("T")[0], "%Y-%m-%d").strftime("%d_%m_%Y")
        host = urlparse(url).hostname
        # partition_key = f'{host}_{date}'
        # if partition_key in self.partition_key_list:
        # url_md5 = util.get_md5(url)
        partition_key = update_time
        self.partition_key_list.append(partition_key)
        # date = datetime.datetime.now().strftime("%d_%m_%Y")

    def upload(self, data, output_type="db"):
        self.fix_data(data)
        if output_type == 'db':
            self.upload_db(data)
            return
        # for k, v in data.items():
        #     self.log.debug("{}: {}".format(k, v))
        # if self.columns_list:
        #     columns = self.columns_list
        # else:
        #     # columns = list(self.data_list[0].keys())
        #     columns = list(data.keys())
        #
        # temp_list = [list(data.values())]
        # sheet_name = 'Sheet1'
        # if data.get('post_type') == "comment":
        #     file_name = "{}-评论.xlsx".format(data.get("site_name", self.file_name))
        #     if not os.path.exists(file_name):
        #         pd.DataFrame(temp_list, columns=columns).to_excel(file_name, index=None)
        #         return
        # else:
        #     file_name = "{}{}-{}.xlsx".format(data.get("site_name", self.file_name), "-修复", datetime.datetime.now().strftime("%Y-%m-%d"))
        #     if not os.path.exists(file_name):
        #         pd.DataFrame(temp_list, columns=columns).to_excel(file_name, index=None)
        #         return
        # # file_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        # df = pd.DataFrame(temp_list, columns=columns)  # 列表数据转为数据框
        # df1 = pd.DataFrame(pd.read_excel(file_name, sheet_name=sheet_name))  # 读取原数据文件和表
        # writer = pd.ExcelWriter(file_name, engine='openpyxl')
        # book = load_workbook(file_name)
        # writer.book = book
        # writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        # df_rows = df1.shape[0]  # 获取原数据的行数
        # df.to_excel(writer, sheet_name=sheet_name, startrow=df_rows + 1, index=False,
        #             header=False)  # 将数据写入excel中的aa表,从第一个空行开始写
        # writer.save()  # 保存
        # if self.time_sleep:
        #     time.sleep(random.randint(self.time_sleep[0], self.time_sleep[1]))

    def upload_db(self, data):
        if not self.collection_name:
            self.log.debug("no collection name")
            sys.exit(1)
        self.counts += 1
        # self.db[self.collection].update_one({'url': url}, {'$set': temp_dict}, upsert=True)
        if self.counts % 10 == 0:
            self.log.info("have stored items count:{}".format(self.counts))
        if len(self.items_list) % 10 == 0:
            update_operations = []
            for item in self.items_list:
                key_field = item.get(self.key_field)
                op = UpdateOne({self.key_field: key_field}, {'$set': item}, upsert=True)
                update_operations.append(op)
            while True:
                try:
                    self.db.db[self.collection_name].bulk_write(update_operations, ordered=False)
                    break
                except Exception as e:
                    self.log.exception(e)
                    time.sleep(10)
            self.log.info("write db counts: {} done".format(self.counts))
            self.items_list = []

    def check_upload_db(self):
        if self.items_list:
            update_operations = []
            for item in self.items_list:
                key_field = item.get(self.key_field)
                op = UpdateOne({self.key_field: key_field}, {'$set': item}, upsert=True)
                update_operations.append(op)
            while True:
                try:
                    self.db.db[self.collection_name].bulk_write(update_operations, ordered=False)
                    break
                except Exception as e:
                    self.log.exception(e)
                    time.sleep(10)
            self.log.info("update db counts: {} done".format(self.counts))
            self.items_list = []

    def format_time(self, time_str):
        time_str = time_str.replace("：", "").replace("时间", "").strip()
        try:
            # e.g. 2021-01-13T04:47:25.672+00:00
            time_str = datetime.datetime.strptime(time_str, '%d %B %Y').strftime("%Y-%m-%d")
            # time_str = datetime.datetime.strptime(time_str, '%d %B %Y').replace(tzinfo=None).isoformat(timespec='milliseconds')

            return time_str
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(time_str, '%B %d, %Y,').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(time_str, '%B %d, %Y').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            extract_time = util.re_find_one("[0-9-: /年月日时分秒\.T]+", time_str)
        except:
            return ""
        try:
            format_time = datetime.datetime.strptime(extract_time, '%d/%m/%Y').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%m/%d/%Y').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y-%m-%d').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y.%m.%d').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%d.%m.%Y').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%d-%m-%Y').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y/%m/%d').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y-%m-%d%H:%M:%S').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y-%m-%d %H:%M').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y-%m-%d%H:%M').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y/%m/%d %H:%M:%S').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y%m%d %H:%M').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y%m%d%H:%M').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y年%m月%d日').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y年%m月%d日%H:%M时').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y年%m月%d日%H时%M分%S秒').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%m月%d日%H:%M').strftime('2022-%m-%d')
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y年%m月%d日%H时%M分').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y年%m月%d日%H:%M').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y%m/%d').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y-%m-%dT%H:%M:%S').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        try:
            format_time = datetime.datetime.strptime(extract_time, '%Y 年 %m 月 %d 日 %H 时 %M 分 ').strftime("%Y-%m-%d")
            return format_time
        except:
            pass
        return ""


if __name__ == "__main__":
    t = TaskBase()
    ts = '4 March 2023'
    s = t.format_time(ts)
    print(s)