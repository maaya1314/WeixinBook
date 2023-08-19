#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author  gikieng.li
# @Date    2017-02-24 22:49
import json

import time

from bdp.i_crawler.i_extractor.ttypes import *
from libs.tools import get_url_info, url_encode

def packet(topic_id,url, data):
    extract_info = ExtractInfo()
    extract_info.ex_status = 2
    extract_info.topic_id = topic_id
    extract_info.extract_data = json.dumps(data)
    url = url_encode(url)
    url_info = get_url_info(url)
    base_info = BaseInfo(url=url,
                         url_id= url_info.get("url_id"),
                         domain= url_info.get("domain"),
                         domain_id= url_info.get("domain_id"),
                         site= url_info.get("site"),
                         segment_id=url_info.get("segment_id"),
                         site_id= url_info.get("site_id")
    )
    crawl_info = CrawlInfo()
    crawl_info.content = ""
    crawl_info.download_time = int(time.time())
    pinfo = PageParseInfo()
    pinfo.crawl_info = crawl_info

    pinfo.base_info = base_info
    pinfo.extract_info = extract_info
    return pinfo