#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time: 2021/11/21 下午6:38
@Author: CZC
@File: json_to_excel.py
"""
import json
import re

import pandas as pd
from openpyxl import load_workbook
import os
import datetime
import sys
sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
from sites.common.connectdb import MongoDB, AppDB


class mongoToExcel(object):
    def __init__(self, collect_name, columns_list, prefix_output_file='./output_files', query="", result_name="", app_db=AppDB):
        self.data_list = []
        self.id_list = []
        self.del_old_flag = True
        self.prefix_output_file = prefix_output_file
        self.collect_name = collect_name
        self.result_name = result_name if result_name else collect_name
        self.db_conf = app_db
        self.query = query
        if not query:
            self.query = {}
        # self.query = {"channel": "其他类别"}
        self.limit = 50000
        # self.columns_list = ['defendant_list', 'max_money', 'case_date', 'bulletin_date', 'litigant_list', 'case_cause', 'court', 'title', 'chain_case_id', 'province', 'litigants', 'case_name', 'case_id', 'judge_content', 'doc_content', 'plaintiff_list', 'case_type', 'third_party_list', 'doc_id', 'procedure',]
        self.columns_list = columns_list
        self.db = None

    def upload(self, file_index=0):
        # temp_list = [list(i.values()) for i in self.data_list]
        if self.columns_list:
            columns = self.columns_list
        else:
            columns_lens = 0
            columns_index = 0
            for i, v in enumerate(self.data_list):
                if len(v) >= columns_lens:
                    columns_lens = len(v)
                    columns_index = i
            columns = list(self.data_list[columns_index].keys())
        temp_list = []
        for i in self.data_list:
            tmp2 = []
            for j in columns:
                value = str(i.get(j, "")).replace("\n", "").replace("\r", "").replace("	", "")
                ILLEGAL_CHARACTERS_RE = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]')
                value = ILLEGAL_CHARACTERS_RE.sub(r'', value)
                tmp2.append(value)
            temp_list.append(tmp2)
        # temp_list = [[i.get(j, "") for j in columns] for i in self.data_list]
        sheet_name = 'Sheet1'
        file_name = "{}/{}{}.xlsx".format(self.prefix_output_file, self.collect_name, "_{}".format(file_index) if file_index else "")
        if self.result_name:
            file_name = "{}/{}{}.xlsx".format(self.prefix_output_file, self.result_name, "_{}".format(file_index) if file_index else "")
        if self.del_old_flag and os.path.exists(file_name):
            os.remove(file_name)
            self.del_old_flag = False
        if not os.path.exists(file_name):
            pd.DataFrame(temp_list, columns=columns).to_excel(file_name, index=None)
            return

            # file_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        df = pd.DataFrame(temp_list, columns=columns)  # 列表数据转为数据框
        df1 = pd.DataFrame(pd.read_excel(file_name, sheet_name=sheet_name))  # 读取原数据文件和表
        writer = pd.ExcelWriter(file_name, engine='openpyxl')
        book = load_workbook(file_name)
        writer.book = book
        writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        df_rows = df1.shape[0]  # 获取原数据的行数
        df.to_excel(writer, sheet_name=sheet_name, startrow=df_rows + 1, index=False, header=False)  # 将数据写入excel中的aa表,从第一个空行开始写
        writer.save()  # 保存
        self.data_list = []

    def read_file(self):
        self.db = MongoDB(self.db_conf)
        # cursor = self.db.db[self.collect_name].find({}, no_cursor_timeout=True)

        if self.limit:
            cursor = self.db.db[self.collect_name].find(self.query, limit=self.limit, no_cursor_timeout=True)
        else:
            cursor = self.db.db[self.collect_name].find(self.query, no_cursor_timeout=True)
        for item in cursor:
            if item.get("_id"):
                item.pop("_id")
            # winner_list = item.get("bid_winner").split(",")
            # if not winner_list:
            #     yield item
            # else:
            #     for winner in winner_list:
            #         item["bid_winner"] = winner
            #         yield item
            yield item

    def run(self):
        counts = 0
        file_index = 0
        for d in self.read_file():
            counts += 1
            self.data_list.append(d)
            if counts % 1000 == 0:
                print(counts)
            if counts % 500000 == 0:
                file_index += 1
                self.upload(file_index)
                self.data_list = []
        if self.data_list:
            if file_index:
                file_index += 1
            self.upload(file_index)
        print(counts)


if __name__ == '__main__':
    coll_name = ''
    col_list = []
    jte = mongoToExcel(coll_name, col_list)
    jte.run()
