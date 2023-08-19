#!/usr/bin/env python
# coding:utf-8
from io import BytesIO

from requests import Session

from libs.loghandler import getLogger
from mfileclient import MFileClient
from thread_pool import ThreadPool
from tools import get_url_info

logger = getLogger()


class ContentLengthError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


default_retry = 3
chunk_size = 1024 * 1024 * 8
max_packet_num = 100
default_timeout = (10, 60)
default_headers = {
    "User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)"
}


class Fetcher(Session):
    def __init__(self, mongo_database, thread_num=32):
        Session.__init__(self)
        self.__asyn_pool = ThreadPool(thread_num=thread_num, task_max_size=612)
        self.__mongo_database = mongo_database

    def __range_download(self, url, file_size, **kwargs):
        packet_num = min((file_size + chunk_size - 1) / chunk_size, 100)
        packet_size = file_size / packet_num
        bi = BytesIO()
        headers = default_headers if not kwargs.get("headers") else kwargs.get("headers")
        for i in xrange(0, packet_num - 1):
            headers["Range"] = "bytes={}-{}".format(packet_size * i, packet_size * (i + 1))
            logger.info("%s\tRange:%s" % (url, headers['Range']))
            resp = self.get(url, headers=headers, timeout=(3 * 60, 3600))
            bi.seek(packet_size * i)
            bi.write(resp.content)
        bi.seek(packet_size * (packet_num - 1))
        headers['Range'] = "bytes={}-".format(packet_size * (packet_num - 1))
        resp = self.get(url, headers=headers, timeout=(3 * 60, 3600))
        bi.write(resp.content)
        return bi.getvalue()

    # TODO 加一些钩子做请求统计
    def get(self, url, **kwargs):
        try_cnt = 0
        max_try = kwargs.get("retry", default_retry)
        last_error = None
        if not kwargs.get("timeout"):
            kwargs['timeout'] = default_timeout
        while try_cnt < max_try:
            try:
                try_cnt += 1
                resp = self.request("GET", url, **kwargs)
                logger.info("GET-SUCCESS:{}\t{}".format(url, resp.status_code))
                return resp
            except Exception as e:
                last_error = e
                logger.warn("GET-FAILED:{}\ttry:\t{}".format(url, try_cnt, e))
        raise last_error

    # TODO 加一些钩子做请求统计
    def post(self, url, data=None, json=None, **kwargs):
        try_cnt = 0
        max_try = kwargs.get("retry", default_retry)
        last_error = None
        if not kwargs.get("timeout"):
            kwargs['timeout'] = default_timeout
        while try_cnt < max_try:
            try:
                try_cnt += 1
                resp = self.request("POST", url, data=data, json=json, **kwargs)
                logger.info("POST-SUCCESS:{}\t{}".format(url, resp.status_code))
                return resp
            except Exception as e:
                last_error = e
                logger.warn("POST-FAILED:{}\ttry:\t{}".format(url, try_cnt, e))
        raise last_error

    def _get(self, url, kwargs):
        return self.get(url, **kwargs)

    def async_get(self, url, callback, **kwargs):
        self.__asyn_pool.queue_task(self._get, (url, kwargs), callback)

    def _post(self, url, kwargs):
        kwargs['url'] = url
        return self.post(**kwargs)

    def async_post(self, url, callback, **kwargs):
        self.__asyn_pool.queue_task(self._post, (url, kwargs), callback)

    def download_file(self, url, save=True, filename=None, force=False, range=False, check_size=True, **kwargs):
        """
        :param url: 要请求的url
        :param save: 是否保存到mongo
        :param force: 是否强制从原网页拉数据,配合save可以强制更新固定url的文件
        :param kwargs:
        :return:
        """
        logger.info("DOWNLOAD-START:{}".format(url))
        mfclient = MFileClient(self.__mongo_database)
        url_info = get_url_info(url)
        # 如果非强制下载则优先从库中拿
        kwargs['stream'] = True
        kwargs['timeout'] = (30, 3 * 60)
        resp = self.get(url, **kwargs)
        headers = resp.headers
        content_length = int(resp.headers['Content-Length'])
        if not filename:
            filename = headers.get("content-disposition")
            if not filename:
                filename = url.split("/")[-1]
            else:
                filename = filename.split("=")[-1]
        if not force:
            check_file = mfclient.get_one_by_url(domain=url_info['domain'], url=url, filename=filename)
            if check_file:
                logger.info("FILE-EXISTS:{}".format(url))
                return check_file

        if range:
            resp.close()
            data = self.__range_download(url=url, file_size=content_length)
        else:
            data = resp.content
        if check_size and not len(data) == content_length:
            raise ContentLengthError("{}:{}".format(len(data), content_length))
        if save and data:
            mfclient.put(filename, source_url=url, data=data)
        logger.info("DOWNLOAD-FINISHED:{}\t{}\t{}".format(url, filename, content_length))
        return {"filename": filename, "length": content_length, "data": data, "sourceUrl": url}

    def join_all(self):
        self.__asyn_pool.join_all()
