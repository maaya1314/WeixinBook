#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author  gikieng.li
# @Date    2017-02-18 14:24
import sys
sys.path.append("..")
from hashlib import md5
from datetime import datetime
from gridfs import GridFS
import pymongo
from libs.tools import get_url_info, get_md5, get_md5_i64

__mfile__  = "__mfile__.files"
class  MFileClient():
    def __init__(self, database):
        self.database = database
        self.gfs = GridFS(self.database, '__mfile__')

    def put(self, file_name, source_url, data, slience=True):
        url_info = get_url_info(source_url)
        domain = url_info.get("domain")
        s_id = url_info.get('url_id')
        self.database[domain].create_index('md5', background = True)
        self.database[domain].ensure_index([("s_id", pymongo.ASCENDING), ("filename", pymongo.ASCENDING)],  background = True)
        self.database["__mfile__.files"].create_index("md5", background = True)
        f_md5 = md5(data).hexdigest()
        __exist = self.gfs.find_one({"md5":f_md5})
        if not __exist:
            new_file = self.gfs.new_file(filename=file_name, source_url=source_url, refs=0)
            new_file.write(data)
            new_file.close()
        now = datetime.now()
        self.database[domain].insert({"filename":file_name,
                                      "sourceUrl":source_url,
                                      'md5':f_md5,
                                      "_utime":str(now),
                                      "_in_time": str(now),
                                      "s_id":s_id,
                                      "length":len(data)
                                      })
        self.database['__mfile__.files'].update({'md5':f_md5}, {"$inc":{"refs":1}})
        return True

    def get_many(self, domain, query = {}, limit=0):
        gfs = GridFS(self.database, '__mfile__')
        for item in self.database[domain].find(query).limit(limit):
            one = gfs.find_one({'md5':item['md5']})
            if one:
                yield {
                    "filename":item['filename'],
                    "length":item['length'],
                    'sourceUrl':item['sourceUrl'],
                    "data":one.read()
                }
    def list_many(self, domain, query = {}, limit=0):
        for item in self.database[domain].find(query).limit(limit):
            yield {
                "filename":item['filename'],
                "length":item['length'],
                "sourceUrl":item['sourceUrl']
            }

    def get_one_by_url(self, domain, url, filename = None):
        s_id = get_md5_i64(url)
        gfs = GridFS(self.database, '__mfile__')
        query = {"s_id": s_id}
        if filename:
            query['filename'] = filename
        for item in self.database[domain].find(query).limit(1):
            one = gfs.find_one({'md5':item['md5']})
            result = {
                "filename":item['filename'],
                "length":item['length'],
                "sourceUrl":item['sourceUrl'],
                "data":one.read()
            }
            return result
        return None

    def exists(self, domain, url, filename):
        s_id = get_md5_i64(url)
        query = {"s_id": s_id}
        if filename:
            query['filename'] = filename
        return self.database[domain].find_one(query) != None

    def remove(self, domain, query={}, limit=0):
        for item in self.database[domain].find(query).limit(limit):
            fmd5 = item['md5']
            gfs = GridFS(self.database, "__mfile__")
            one = gfs.find_one({"md5":fmd5})
            if one:
                gfs.delete(one._id)
            self.database[domain].remove({"_id":item['_id']})
