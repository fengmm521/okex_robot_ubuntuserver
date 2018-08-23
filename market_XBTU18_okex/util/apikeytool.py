#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
#客户端调用，用于查看API返回结果

import json
import os

from magetool import pathtool

nfpth = os.path.abspath(__file__)
ndir,_ = os.path.split(nfpth)
ppdir = pathtool.GetParentPath(pathtool.GetParentPath(pathtool.GetParentPath(ndir))) + os.sep + 'btc/okexapikey/okexapikey.txt'
print(ppdir)
f = open(ppdir,'r')
tmpstr = f.read()
f.close()

apikeydic = json.loads(tmpstr)

#初始化apikey，secretkey,url
# apikey = apikeydic['okex']['apikey']
# secretkey = apikeydic['okex']['secretkey']
