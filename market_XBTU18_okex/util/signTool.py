#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8

import sys
from sys import version_info  

if version_info.major < 3:
    reload(sys)
    sys.setdefaultencoding('utf-8')

import json
import os
import hashlib
import json


    



import platform

def getSysType():
    sysSystem = platform.system()
    if sysSystem == 'Windows':  #mac系统
        return 'win'
    elif sysSystem == 'Darwin':
        return 'mac'
    elif sysSystem == 'Linux':
        return 'linux'

#python2和3字典，list编译转换
def byteify(data):
    if type(data) == str:
        return data
    elif type(data) == list:
        return str(data)
    elif type(data) == dict:
        outstr = ''
        ks = sorted(data.keys(),reverse = True)
        for k in ks:
            outstr += k
            tmpstr = byteify(data[k])
            outstr += tmpstr
        return outstr
    else:
        return str(data)

def isSignOK(msgdic,secretkey):
    # utf8dict = byteify(msgdic['data'])
    # dicttmp = sorted(msgdic['data'].items(), key=lambda d:d[0], reverse = True)  
    dictstr = byteify(msgdic['data'])
    data = str(dictstr) + str(msgdic['time'])  + str(secretkey)
    # data = json.dumps(msgdic['data']) + str(msgdic['time'])  + str(secretkey)
    csgin = msgdic['sign']
    if csgin == 'test':
        return True
    print(type(data))
    print(data)
    sgin = hashlib.sha256(data.encode('utf-8')).hexdigest().upper()
    print(sgin)
    
    if csgin == sgin:
        return True
    else:
        return False

def signMsg(msgdic,ptime,secretkey):
    if type(msgdic) == str:
        data = msgdic + str(ptime)  + str(secretkey)
        print(type(data))
        print(data)
        sgin = hashlib.sha256(data.encode()).hexdigest().upper()
        return sgin
    if type(msgdic) == bytes:
        data = msgdic.decode('utf-8') + str(ptime)  + str(secretkey)
        sgin = hashlib.sha256(data.encode()).hexdigest().upper()
        return sgin
    else:
        # utf8dict = byteify(msgdic)
        # dicttmp= sorted(msgdic.items(), key=lambda d:d[0], reverse = True) 
        # data = str(dicttmp)  + str(ptime)  + str(secretkey) 
        dictstr = byteify(msgdic)
        data = str(dictstr)  + str(ptime)  + str(secretkey) 
        # data = json.dumps(msgdic)  + str(ptime)  + str(secretkey)
        print(type(data))
        print(data)

        sgin = hashlib.sha256(data.encode()).hexdigest().upper()
        return sgin