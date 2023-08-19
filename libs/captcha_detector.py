#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author  gikieng.li
# @Date    2017-03-10 16:33
import base64
import json
import sys
sys.path.append("..")
sys.path.append("../..")
from libs.fetcher import Fetcher
from libs.loghandler import getLogger
from conf import m_settings

logger = getLogger()
class CaptchaDetectorError(Exception):
    def __init__(self, *args, **kwargs):  # real signature unknown
        Exception.__init__(*args, **kwargs)


class Remote_CaptchaDetector():
    def __init__(self):
        self.remote_server_host = m_settings.CAPTCHA_HOST
        self.fetcher = Fetcher(mongo_database=None)

    def detect(self, img_content, codetype, use, detector = "remote"):
        data = {'codetype': codetype,
                'base64_pic': base64.b64encode(img_content),
                'user': 'mfiledownload',
                'use': use
        }
        resp = self.fetcher.post(self.remote_server_host, data=data)
        orc_result = json.loads(resp.content)
        print orc_result
        if not orc_result['err_str'] == u"OK":
            raise CaptchaDetectorError()

        return orc_result['pic_str']


class CaptchaDetector():
    def __init__(self):
        self.detector = {
            "remote":Remote_CaptchaDetector()
        }

    def detect(self, img_content, codetype, use, detector_name = "remote"):
        detector = self.detector.get(detector_name)
        return detector.detect(img_content=img_content, codetype=codetype, use=use)