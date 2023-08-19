#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author  gikieng.li
# @Date    2017-02-21 15:4

"""
这个是模板配置文件,使用的时候复制一份命名为m_settings.py
切记不要上传m_settions.py
"""
import os

from pymongo import MongoClient

# from libs.pybeanstalkd import PyBeanstalk

BEANSTALKD = {
    # 离线
    "host": "192.168.0.92",
    "port": 11300
}

BEANSTALKD2 = {
    "host": "192.168.0.92",
    "port": 11300
}

BEANSTALKD3 = {
    "host": "192.168.0.93",
    "port": 11400
}

# 融合逻辑消息队列
MERGE_MQ_CONF = {
    'host': '192.168.0.93',
    'port': 11300,
    'tube': 'extract_info'
}

# 融合逻辑消息队列,测试环境
MERGE_MQ_CONF_TEST = {
    'host': '192.168.1.232',
    'port': 11300,
    'tube': 'extract_info'
}

ONLINE_BEANSTALKD2 = {
    # 线上
    "host": "172.18.180.223",
    "port": 11300
}

BEANSTALKD_TUBE = {
    # 离线消息队列名字
    "extract_info": "offline_extract_info",
    "download_rsp": "offline_download_rsp",
    "download_req": "offline_download_req",

    "online_extract_info": "extract_info",
    "online_download_rsp": "download_rsp",
    "online_download_req": "download_req",

    # 新版工商 新注册企业采集队列
    "company_collection": "company_collection"
}

TOPICS = {
    "judgement_wenshu": 32,
    "court_ktgg": 34,
    "enterprise_owing_tax": 35,
    "zhixing_info": 42,
    "shixin_info": 38,
    'patent': 43,
    "bid_detail": 41,
    "registration_company": 231,
    'baidu_news': 40,
    'environment_protection_information': 225,
    'news': 79,
    'land_value': 230,
    'financial_announcement': 232,
    'increasing_selling_announcement': 233,
    'top_ten_shareholder': 234,
    'bulletin': 33,
    'tax_payer_level_A_new': 219,
    'investment_events': 116,
    'judge_process': 37,
    'ppp_project': 100,
    'xiaoqu_lianjia': 99,
    'ershoufang_lianjia': 103,
}

SCHEDULER_REDIS = {
    "host": "192.168.0.90",
    "port": 6379,
    "password": "haizhi@)",
    "db": 0
}

MFILE_MONGO_BACKEND = {
    "host": "192.168.0.88",
    "port": 27002,
    "user": 'work',
    "password": 'n%y$YuL*nVFZ0KSP'
}

MONGO_BACKEND = {
    "host": "192.168.0.87",
    "port": 27001,
    "user": 'work',
    "password": 'n%y$YuL*nVFZ0KSP'
}
CAPTCHA_HOST = "http://172.18.180.225:9820/cap_ocr"

PROJECTDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOGDIR = os.path.join(PROJECTDIR, "logs")

LOCAL_FILE_BASE_DIR = os.path.join(PROJECTDIR, "data")

PROXY_HOST = "http://172.18.180.224:8571"


def mfile_database():
    client = MongoClient(host=MFILE_MONGO_BACKEND['host'], port=MFILE_MONGO_BACKEND['port'])
    database = client['mfile']
    if MFILE_MONGO_BACKEND['user'] and MFILE_MONGO_BACKEND['password']:
        database.authenticate(MFILE_MONGO_BACKEND['user'], MFILE_MONGO_BACKEND['password'])
    return database


def beanstalk_client():
    # 离线
    return PyBeanstalk(BEANSTALKD["host"], BEANSTALKD['port'])


def beanstalk_client2():
    return PyBeanstalk(BEANSTALKD2["host"], BEANSTALKD2['port'])


def beanstalk_client3():
    return PyBeanstalk(BEANSTALKD3["host"], BEANSTALKD3["port"])


def online_beanstalk_client():
    # 线上
    return PyBeanstalk(ONLINE_BEANSTALKD2["host"], ONLINE_BEANSTALKD2["port"])
