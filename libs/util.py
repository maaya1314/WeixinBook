# coding=utf-8
'''
公共方法.
'''
import ctypes
import decimal
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time
import gc
import datetime

# def strQ2B(ustring):
#     """全角转半角"""
#     rstring = ""
#     for uchar in ustring:
#         inside_code = ord(uchar)
#         if inside_code == 12288:  # 全角空格直接转换
#             inside_code = 32
#         elif 65281 <= inside_code <= 65374:  # 全角字符（除空格）根据关系转化
#             inside_code -= 65248
#
#         rstring += unichr(inside_code)
#     return rstring
#
#
# def strB2Q(ustring):
#     """半角转全角"""
#     rstring = ""
#     for uchar in ustring:
#         inside_code = ord(uchar)
#         if inside_code == 32:  # 半角空格直接转化
#             inside_code = 12288
#         elif 32 <= inside_code <= 126:  # 半角字符（除空格）根据关系转化
#             inside_code += 65248
#
#         rstring += unichr(inside_code)
#     return rstring
try:
    import urlparse
except:
    from urllib import parse as urlparse
import zlib

import chardet
from tld import get_tld

pat_ymd = re.compile(u'(\d+)')


# def format_date(beforedate):
#     str_group = re.findall(pat_ymd, beforedate if beforedate is not None else '')
#     if beforedate is not None and beforedate != '' and len(str_group) == 3:
#         yy = str(str_group[0])
#         mm = str(str_group[1])
#         dd = str(str_group[2])
#         if len(yy) < 2:
#             raise StandardError('formdate_error:' + str(str_group))
#         if len(mm) < 2:
#             mm = '0' + mm
#         if len(dd) < 2:
#             dd = '0' + dd
#         date = '{0}-{1}-{2}'.format(yy, mm, dd)
#     else:
#         date = beforedate
#     return date


def format_content(content=u''):
    tmpcontent = content
    if content is not None and content.strip() != u'':
        tmpcontent = content.replace(u'收起更多', u'').replace(u'更多', u'')
    return tmpcontent


def get_match_value(rule_prefix, rule_suffix, text, return_multi=False, default_match="([\s\S]*?)"):
    change_rule = rule_prefix + default_match + rule_suffix
    res = re.findall(re.compile(change_rule), text)
    if len(res) > 0:
        if not return_multi:
            tmp_str = res[0].replace(rule_prefix, '').replace(rule_suffix, '')
            return tmp_str
        return res
    else:
        if not return_multi:
            return ""
        return [""]


def json_loads(text):
    try:
        return json.loads(text)
    except Exception:
        return None


def get_time_stamp():
    return str(int(time.time() * 1000))


def get_cur_time():
    return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())


def get_change_stamp(str_time):
    return int(time.mktime(time.strptime(str_time, '%Y-%m-%d %H:%M:%S')))


# 从时间戳转换成时间格式 时间戳是10位的
def from_time_stamp_to_time(time_stamp):
    time_local = time.localtime(time_stamp)
    return time.strftime("%Y-%m-%d %H:%M:%S", time_local)


# 从时间戳转换成时间格式 时间戳是13位的
def from_13stamp_to_time(time_stamp):
    if not time_stamp:
        return time_stamp
    if isinstance(time_stamp, str):
        try:
            time_stamp = int(time_stamp)
        except:
            return time_stamp
    time_local = time.localtime(time_stamp/1000)
    return time.strftime("%Y-%m-%d %H:%M:%S", time_local)


def format_time(original_time):
    if not original_time:
        return original_time

    if isinstance(original_time, str):
        try:
            original_time = int(original_time)
        except:
            return original_time

    if len(str(original_time)) == 10:
        return from_time_stamp_to_time(original_time)
    elif len(str(original_time)) == 13:
        return from_13stamp_to_time(original_time)


# def get_format_time(str_time):
#     if not str_time:
#         return
#     return time.mktime(time.strptime(str_time, '%Y-%m-%d %H:%M:%S'))


def get_pid_log_name(log_name):
    return log_name + '_' + str(os.getpid()) + '.log'


def sub_time(cur_time, pre_time):
    cur_localtime = time.mktime(time.strptime(cur_time, '%Y-%m-%d %H:%M:%S'))
    pre_localtime = time.mktime(time.strptime(pre_time, '%Y-%m-%d %H:%M:%S'))
    sub_second = int(cur_localtime - pre_localtime)
    return sub_second


def get_now_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_gm_time():
    return time.strftime(u"%a %b %d %Y %H:%M:%S GMT+0800 (CST)", time.gmtime(time.time() + 8 * 60 * 60))


def get_gm_cn_time():
    return time.strftime(u"%a %b %d %Y %H:%M:%S GMT 0800 (中国标准时间)", time.gmtime(time.time() + 8 * 60 * 60))


def get_random_num():
    x = [random.random()]
    decimal.getcontext().prec = 16
    return decimal.Decimal(x[0]) * 1


def get_yesterday():
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    return str(yesterday)


def get_format_time(days=0):
    if not days:
        days = 0
    now_time = datetime.datetime.now()
    new_time = now_time + datetime.timedelta(days=days)
    # 格式化输出
    return str(new_time.strftime('%Y-%m-%d'))


# 过滤无效数据
def check_html(text):
    if text.find('无效用户') != -1 and text.find('Unauthorized') != -1:
        return False
    return True


# 生成mongodb存储ID
def generator_id(param_dict, company, province):
    hash_key = ''
    for key, value in param_dict.iteritems():
        hash_key += str(value) + '#'
    hash_key += company + '#'
    hash_key += province + '#'
    return hashlib.sha256(hash_key).hexdigest()


def re_find_one(pattern, string):
    datas = re.findall(pattern, string)
    if len(datas) > 0:
        return datas[0]
    return None


def re_find(pattern, string, multi=False):
    datas = re.findall(pattern, string)
    if len(datas) > 0:
        if multi:
            return datas
        return datas[0]

    return None

money_regex = re.compile(u'\d+\.\d+|\d+')
money_map = {
    u"亿": 100000000, u"亿元": 100000000,
    u"万": 10000, u"M": 1000000, u"万元": 10000,
    u"千": 1000, u'百': 100
}

money_type_list = {
    u'美元': u'美元', u"USD": u"美元",
    u"元": u"人民币", u"RMB": u"人民币", u"人民币": u"人民币",
    u'欧元': u'欧元', u"EUR": u"欧元",
    u'镑': u'英镑', u"GBP": u"英镑",
    u'日元': u'日元', u"JPY": u"日元",
    u'韩币': u'韩币', u"KRW": u"韩币",
    u'港币': u'港币', u'HKD': u'港币'
}


# def transfer_money(src_money, out_money_unit=u'', skip_none=True, high2low=True):
#     '''
#     :param src_money:
#     :param out_money_unit:
#     :return: 金额,单位,货币
#     '''
#     digit = 0
#     if src_money is None or src_money == '':
#         src_money = digit
#     ccy = u''
#     try:
#         src_money = unicode(src_money).replace(',', '')
#         ret = re_find_one(money_regex, src_money)
#         if ret:
#             try:
#                 digit = float(ret)
#             except:
#                 pass
#         if ret is None and not skip_none:
#             return src_money, out_money_unit, ccy
#     except:
#         return src_money, out_money_unit, ccy
#
#     money = digit
#     for key, value in money_map.items():
#         if key in unicode(src_money):
#             money = digit * value
#             break
#
#     ccy = u'人民币'
#     for money_type_k, money_type_v in money_type_list.items():
#         if money_type_k in unicode(src_money):
#             ccy = money_type_v
#             break
#     real_money = money * money_map.get(out_money_unit) if high2low else  money / money_map.get(out_money_unit)
#     money = str(money if out_money_unit == '' else real_money)
#     return money, out_money_unit, ccy
#

# def timestampToTimestr(timestamp, format='%Y-%m-%d %H:%M:%S'):
#     return time.strftime(format, time.localtime(timestamp))

def get_amount_unit(py_th, default_dom='th'):
    default_amount = u'万元人民币'
    if py_th is None:
        return
    text = py_th.find(default_dom).text()
    index = text.find(u'(币种：')
    amount = default_amount if index == -1 else text[index + 4:text.find(u') 实缴明细')]
    return amount


# 添加单位
def get_amount_with_unit(text, unit=u'万元'):
    text = text.replace(u'\xa0', u'')
    text = str(text).strip()
    if text == u'':
        return u'0万元'
    return text + unit


# url 参数解析
def get_url_param(url):
    param = {}
    if url is None or url.strip() == '':
        return param
    # 去除等号
    url = url.replace(' ', '')
    if '?' not in url:
        return param
    try:
        part = url.split('?')
        if len(part) < 2:
            return {}

        part_list = part[1].split('&')
        for item in part_list:
            item_part = item.split('=')
            if len(item_part) < 2:
                continue
            param[item_part[0]] = item_part[1]
    except:
        return param

    return param


# 判断页面是否为拦截页面
def judge_feature(content):
    feature_list = ['val2.bangruitech.com',
                    'val.bangruitech.com',
                    '请不要使用非法的URL地址访问',
                    '您正在试图非法攻击',
                    '您访问的URL地址不被允许']
    for feature in feature_list:
        if feature in content:
            return True

    return False


# 获得系统版本信息
def get_system_info():
    import platform
    system = platform.system()
    if system == 'Darwin':
        return 'mac'
    if system == 'Linux':
        return 'linux'
    return 'linux'


def run_cmd(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while True:
        line = p.stdout.readline()
        if line:
            sys.stdout.flush()
        else:
            break
    p.wait()


def run_shell(shell):
    p = subprocess.Popen(shell, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
    line = p.stdout.readline()
    if line:
        sys.stdout.flush()
    p.communicate()
    gc.collect()


def decompress_zlib(content, is_file=True):
    decompress = zlib.decompressobj()
    if is_file:
        zlib_file = open(content, 'rb')
        data = zlib_file.read(1024)
    else:
        data = content
    content = decompress.decompress(data)
    return content


def get_encoding(content):
    if not isinstance(content, bytes):
        content = content.encode()
    return chardet.detect(content).get('encoding')


def get_md5(string):
    m2 = hashlib.md5()
    m2.update(string.encode())
    return m2.hexdigest()


def get_md5_i64(obj):
    m = hashlib.md5()
    m.update(obj)
    return ctypes.c_int64(int(m.hexdigest()[8:-8], 16)).value


def get_url_info(base_url):
    url_split = urlparse.urlsplit(base_url)
    url_info = dict()
    url_info['site'] = url_split.netloc
    url_info['site'] = url_info['site'].split(':')[0]
    url_info['site_id'] = get_md5_i64(url_info['site'])
    url_info['path'] = url_split.path
    url_info['query'] = url_split.query
    url_info['fragment'] = url_split.fragment
    try:
        url_info['domain'] = get_tld(base_url)
    except Exception as e:
        url_info['domain'] = url_info['site']
    if url_info.get('domain'):
        url_info['domain_id'] = get_md5_i64(url_info['domain'])
    else:
        url_info['domain_id'] = None

    url_info['url'] = base_url
    url_info['url_id'] = get_md5_i64(base_url)
    return url_info


# 去除none属性
def del_none(data):
    if data == 'None' or data is None:
        return ''

    if isinstance(data, list):
        data_copy = []
        for item in data:
            if item == 'None' or item is None:
                data_copy.append('')
            if isinstance(item, list):
                data_copy.append(del_none(item))
            elif isinstance(item, dict):
                data_copy.append(del_none(item))
            else:
                data_copy.append(item)
        return data_copy

    if isinstance(data, dict):
        for key, value in data.items():
            if value is None or value == 'None':
                data[key] = ''
            if isinstance(value, list):
                data[key] = del_none(value)
            if isinstance(value, dict):
                data[key] = del_none(value)

        return data

    return data


if __name__ == '__main__':
    c = "\xc8\xfd\xd1\xc7\x8dn\xc8\xf0\xcd\xb6\xd7\xca\xd3\xd0\xcf\xde\xb9\xab\xcb\xbe"
    # print get_encoding(c)
    # print c.decode("gb18030")
    # print get_time_stamp()
    # cmd  = """
    # ps -ef|grep -v grep |grep '8050'
    # """
    # c = "ps -ef|grep -v grep |grep '8050:8050'|awk '{{print $2}}'"
    # print run_cmd(cmd)
    # print run_cmd(c)
