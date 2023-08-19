#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
from logging.handlers import RotatingFileHandler

sys.path.append("..")
import logging
from libs import m_settings
import os


# 每一个task实例一个logger
def getLogger(task_name="root", level=logging.INFO, console_out=False):
    logger = logging.getLogger(task_name)
    if isinstance(level, str):
        level = level.lower()
    if level == "debug":
        level = logging.DEBUG
    elif level == "info":
        level = logging.INFO
    elif level == "warning":
        level = logging.WARNING
    elif level == "error":
        level = logging.ERROR
    else:
        level = logging.INFO

    if not os.path.exists(m_settings.LOGDIR):
        os.makedirs(m_settings.LOGDIR)
    LOG_FILE = m_settings.LOGDIR + "/%s.log" % task_name
    fmt = "%(asctime)s - %(filename)s[line:%(lineno)d] %(levelname)s - %(message)s"
    formatter = logging.Formatter(fmt)
    #  这里进行判断，如果logger.handlers列表为空，则添加，否则，直接去写日志
    if not logger.handlers:
        handler = RotatingFileHandler(LOG_FILE, maxBytes=64 * 1024 * 1025, backupCount=5)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        if console_out is True:
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter(fmt)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
    logger.setLevel(level)
    return logger


if __name__ == "__main__":
    d = getLogger('test', level='debug', console_out=True)
    d.info('aaa')