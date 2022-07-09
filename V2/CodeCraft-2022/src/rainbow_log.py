#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@ Author：CJK_Monomania
@ Data：2022-05-19
"""
import sys
import time

''' 
@ 功能：
'''
class RainbowLog:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    def __init__(self, debug_flag=True):
        self.debug_flag = debug_flag

    def log_HEADER(self, msg: str):
        if not self.debug_flag:
            return
        date = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        print(f"[{date}] ", end='')
        print(RainbowLog.HEADER + 'HEADER' + RainbowLog.ENDC, end=': ')
        print(RainbowLog.HEADER + msg + RainbowLog.ENDC)

    def log_OKBLUE(self, msg: str):
        if not self.debug_flag:
            return
        date = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        print(f"[{date}] ", end='')
        print(RainbowLog.OKBLUE + 'OKBLUE' + RainbowLog.ENDC, end=': ')
        print(RainbowLog.OKBLUE + msg + RainbowLog.ENDC)

    def log_OKGREEN(self, msg: str):
        if not self.debug_flag:
            return
        date = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        print(f"[{date}] ", end='')
        print(RainbowLog.OKGREEN+'OKGREEN'+RainbowLog.ENDC, end=': ')
        print(RainbowLog.OKGREEN + msg + RainbowLog.ENDC)

    def log_WARNING(self, msg: str):
        if not self.debug_flag:
            return
        date = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        print(f"[{date}] ", end='')
        print(RainbowLog.WARNING + 'WARNING' + RainbowLog.ENDC, end=': ')
        print(RainbowLog.WARNING + msg + RainbowLog.ENDC)

    def log_FAIL(self, msg: str):
        if not self.debug_flag:
            return
        date = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        print(f"[{date}] ", end='')
        print(RainbowLog.FAIL + 'FAIL' + RainbowLog.ENDC, end=': ')
        print(RainbowLog.FAIL + msg + RainbowLog.ENDC)

    def log_ERROR(self, msg: str):
        if not self.debug_flag:
            return
        date = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        print(f"[{date}] ", end='')
        print(RainbowLog.FAIL + 'ERROR' + RainbowLog.BOLD + RainbowLog.ENDC, end=': ')
        print(RainbowLog.FAIL + msg + RainbowLog.BOLD + RainbowLog.ENDC)


if __name__ == '__main__':
    log = RainbowLog(debug_flag=True)
    msg = 'test'
    log.log_FAIL(msg)
    log.log_ERROR(msg)
    log.log_HEADER(msg)
    log.log_WARNING(msg)
    log.log_OKBLUE(msg)
    log.log_OKGREEN(msg)