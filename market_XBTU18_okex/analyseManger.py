#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
#客户端调用，用于查看API返回结果

import os
import sys
from sys import version_info  

if version_info.major < 3:
    reload(sys)
    sys.setdefaultencoding('utf-8')

import math   

if version_info.major < 3:
    magetoolpth = '/usr/local/lib/python2.7/site-packages'
    if magetoolpth not in sys.path:
        sys.path.append(magetoolpth)
    else:
        print('heave magetool pth')

import socket
import threading
import time
import json

import base64

from magetool import pathtool
from magetool import timetool
sys.path.append('util')
import signTool

import orderObj

import platform

def getSysType():
    sysSystem = platform.system()
    if sysSystem == 'Windows':  #mac系统
        return 'win'
    elif sysSystem == 'Darwin':
        return 'mac'
    elif sysSystem == 'Linux':
        return 'linux'

saylist = []

def sayMsg(msg):
    smsg = msg
    # print smsg
    if getSysType() == 'mac':
        # saylist.append(smsg)
        # if len(saylist) > 5:
        #     saylist = saylist[-5:]
        def sayTradeRun():
            cmd = '/usr/bin/say %s'%(smsg)
            os.system(cmd)
        sTradethr = threading.Thread(target=sayTradeRun,args=())
        sTradethr.setDaemon(True)
        sTradethr.start()
    


class TradeTool(object):
    """docstring for ClassName"""
    def __init__(self,configdic,tradeconfiddic,isTest = True):
        #期货交易工具
        self.configdic = configdic
        self.isTest = isTest

    # "iOkexRate":0.0005,     //okex主动成交费率
    # "pOkexRate":0.0002,     //okex被动成交费率
    # "iBiemexRate":0.00075,  //bitmex主动成交费率
    # "pBiemexRate":-0.00025,   //bitmex被动成交费率
    # "stepPercent":0.005,    //下单网格价格百分比大小
    # "movePercent":0.003,    //网格滑动价格百分比
    # "normTime":3,           //基准价格重新计算时间,单位:小时
    # "reconfigTime":60       //配置文件检测刷新时间，单位:秒
        self.tradeConfig = None
        self.iOkexRate = 0.0005
        self.pOkexRate = 0.0002
        self.iBiemexRate = 0.00075
        self.pBiemexRate = -0.00025
        self.stepPercent = 0.005
        self.movePercent = 0.003
        self.normTime = 3*60*60    #小时换算成秒
        self.startDaly = 0    #服务器开始工作延时，单位为分钟
        #初始仓位，目前为固定值，后期会以差价24小时变动情况动态调整
        self.baseOB = 0             #初始OB仓位
        self.baseBO = 0             #初始BO仓位
        self.basePrice=0          #基础手动下单价格
        self.autoBase = 0           #是否开始24小时基础差价自动调整,0:不开启,1:开启
        self.dalyPrice = 0          #撤单允许波动价范围

        self.isInitOnce = True

        self.initTraddeConfig(tradeconfiddic)

        #okex
        self.okexSeckey = configdic['okex']['secretkey']
        self.okexDataSocket = None
        self.okexDatathr = None
        self.okexTradeSocket = None
        self.okexTradethr = None



        #bitmex
        self.bitmexSeckey = configdic['bitmex']['secretkey']
        self.bitmexDataSocket = None
        self.bitmexDatathr = None
        self.bitmexTradeSocket = None
        self.bitmexTradethr = None


        self.avrOkexBuy = 0.0
        self.avrBitmexBuy = 0.0

        self.avrOkexSell = 0.0
        self.avrBitmexSell = 0.0

        self.avrDelayTime = 1*60*60   #单位:秒

        self.okexBTC = 0.0
        self.bitmexBTC = 0.0

        self.tradeSavePth = 'log/trade.txt'
        
        self.socketstate = {'bd':False,'bt':False,'od':False,'ot':False}

        ptime = int(time.time())
        self.lastimedic = {'bd':ptime,'bt':ptime,'od':ptime,'ot':ptime}


        self.isShowLog = True

        self.okexDatas = []             #买一价，卖一价，接收数据时间
        self.bitmexDatas = []           #买一价，卖一价, 接收数据时间
        self.lastSub = {}               #okex的卖一价和bitmex的买一价的差价，bitmex的卖一价和okex的买一价的差价,时间差,最后接收时间
        self.obsubs = []
        self.bosubs = []
        self.arvsub = 0                 #滑动差值
        self.okexTradeMsgs = []         #bitmex已下单，等待bitmex成交后，再吃单成交的okex

        self.openTrade = []             #保存的开仓对

        self.bCIDBase = 0               #bitmex的用户自定义定单ID基数

        self.bCIDData = {}
        #定单ID生成算法：b_orderType_CIDBase_time
        self.oCIDData = {}

        self.obCount = 0
        self.boCount = 0

        self.toolStartTime = int(time.time())

        self.lastBitmexTradeTime = 0
        self.lastOkexTradeTime = 0

        self.isBitmexDataOK = False
        self.isOkexDataOK = False

        self.isBitmexTradeOK = False
        self.isOkexTradeOK = False

        self.subsavefilename = str(int(time.time())) + '_sub.txt'

        #定单状态
        #0.没有下单，可下新单
        #111.bitmex开多正在下单
        #112.bitmex开多下单已发送，等成交
        #113.bitmex开多正在取消下单
        #114.bitmex部分成交，设置已成交数量更新，同时开相应的okex定单，目前这一状态先不作考虑，后期未成交部分会真对情况作取消和重新下单处理
        #115.bitmex完全成交，开启okex下单

        #121.bitmex开空正在下单
        #122.bitmex开空下单已发送，等成交
        #123.bitmex开空正在取消下单
        #124.bitmex部分成交，设置已成交数量更新，同时开相应的okex定单，目前这一状态先不作考虑，后期未成交部分会真对情况作取消和重新下单处理
        #125.bitmex完全成交，开启okex下单

        #131.bitmex平多正在下单
        #132.bitmex平多下单已发送，等成交
        #133.bitmex平多下单正在取消
        #134.bitmex部分成交，设置已成交数量更新，同时开相应的okex定单，目前这一状态先不作考虑，后期未成交部分会真对情况作取消和重新下单处理
        #135.bitmex完全成交，开启okex下单

        #141.bitmex平空正在下单
        #142.bitmex平空下单已发送，等成交
        #143.bitmex平空下单正在取消
        #144.bitmex部分成交，设置已成交数量更新，同时开相应的okex定单，目前这一状态先不作考虑，后期未成交部分会真对情况作取消和重新下单处理
        #145.bitmex完全成交，开启okex下单

        #0.bitmex取消定单完成,状态变为可开新bitmex定单状态


        #211.okex开多正在下单
        #212.okex开多已发送，等成交
        #213.okex开多正在取消定单
        #214.okex部分成交，设置已成交数量更新，目前这一状态先不作处理，后期会结合已成交bitmex的更新量作重新下单处理
        #215.okex取消开多完成，正在重新下开多定单，状态与211效果相同

        #221.okex开空正在下单
        #222.okex开空已发送，等成交
        #223.okex开空正在取消定单
        #224.okex部分成交，设置已成交数量更新，目前这一状态先不作处理，后期会结合已成交bitmex的更新量作重新下单处理
        #225.okex取消开空完成，正在重新下开空定单,状态与221效果相同

        #231.okex平多正在下单
        #232.okex平多已发送，等成交 
        #233.okex平多正在取消定单
        #234.okex部分成交，设置已成交数量更新，目前这一状态先不作处理，后期会结合已成交bitmex的更新量作重新下单处理
        #235.okex取消平多完成，正在重新下平多定单，状态与231效果相同

        #241.okex平空正在下单
        #242.okex平空已发送，等成交
        #243.okex平空正在取消定单
        #244.okex部分成交，设置已成交数量更新，目前这一状态先不作处理，后期会结合已成交bitmex的更新量作重新下单处理
        #245.okex取消平空完成，正在重新下平空定单，状态与241效果相同

        #0.okex定单完全成交,状态变为可开新bitmex定单状态

        self.tradeState = 0

        self.nowTradeCID = ''

        self.okexOIDDic = {}

        self.tradecount = 0

        self.showLogCount = 0

        self.isCloseBaseOB = False
        self.isCloseBaseBO = False

        self.bitmexTradeStartTime = 0

        self.priceWinlog = []
        self.maxStrlen = 0


        self.clientSoket = None

        self.initSocket()


    def setClientSocket(self,csocket):
        self.clientSoket = csocket

    def sendMsgToClient(self,msg):
        
        if self.clientSoket:
            def sayTradeRun(tmsg):
                try:
                    datdic = {}
                    if type(tmsg) == str:
                        msgtmp = base64.b64encode(tmsg.encode())
                        datdic = {'data':msgtmp.decode(),'state':self.tradeState,'isbase64data':True}
                    else:
                        datdic = {'data':tmsg,'state':self.tradeState,'isbase64data':False}
                    sendstr = json.dumps(datdic)
                    self.clientSoket.send(sendstr.encode())
                except Exception as e:
                    print('client close or erro')
                    self.clientSoket = None
            tmsg = msg
            sTradethr = threading.Thread(target=sayTradeRun,args=(tmsg,))
            sTradethr.setDaemon(True)
            sTradethr.start()
            
            

    def runClientCMD(self,cmdstr):
        data = cmdstr
        tradetool = self
        if data == 'openbo':
            priceOBBuySub = tradetool.okexDatas[0][0] - tradetool.bitmexDatas[0][0] + 10
            tradetool.openBO(subpurce = priceOBBuySub)
        elif data == 'openob':
            priceOBSellSub = tradetool.okexDatas[1][0] - tradetool.bitmexDatas[1][0] - 10
            tradetool.openOB(subpurce = priceOBSellSub)
        elif data == 'closebo':
            priceOBSellSub = tradetool.okexDatas[1][0] - tradetool.bitmexDatas[1][0] - 10
            tradetool.closeBO(subpurce = priceOBSellSub)
        elif data == 'closeob':
            priceOBBuySub = tradetool.okexDatas[0][0] - tradetool.bitmexDatas[0][0] + 10
            tradetool.closeOB(subpurce = priceOBBuySub)
        elif data == 'okexol':
            msg = {'type':'ol','amount':tradetool.baseAmount,'price':1000.0,'islimit':1,'cid':'sssss'}
            tradetool.sendMsgToOkexTrade('ol', msg)
        elif data == 'okexos':
            msg = {'type':'os','amount':tradetool.baseAmount,'price':20000.0,'islimit':1,'cid':'sssss'}
            tradetool.sendMsgToOkexTrade('os', msg)
        elif data == 'okexcl':
            msg = {'type':'cl','amount':tradetool.baseAmount,'price':20000.0,'islimit':1,'cid':'sssss'}
            tradetool.sendMsgToOkexTrade('cl', msg)
        elif data == 'okexcs':
            msg = {'type':'cs','amount':tradetool.baseAmount,'price':1000.0,'islimit':1,'cid':'sssss'}
            tradetool.sendMsgToOkexTrade('cs', msg)
        elif data == 'bitmexol':
            CIDtmp = 'sssss' + str(time.time())
            msg = {'type':'ol','amount':tradetool.baseAmount,'price':1000.0,'islimit':1,'cid':CIDtmp}
            tradetool.sendMsgToBitmexTrade('ol', msg)
        elif data == 'bitmexos':
            CIDtmp = 'sssss' + str(time.time())
            msg = {'type':'os','amount':tradetool.baseAmount,'price':20000.0,'islimit':1,'cid':CIDtmp}
            tradetool.sendMsgToBitmexTrade('os', msg)
        elif data == 'bitmexcl':
            CIDtmp = 'sssss' + str(time.time())
            msg = {'type':'cl','amount':tradetool.baseAmount,'price':20000.0,'islimit':1,'cid':CIDtmp}
            tradetool.sendMsgToBitmexTrade('cl', msg)
        elif data == 'bitmexcs':
            CIDtmp = 'sssss' + str(time.time())
            msg = {'type':'cs','amount':tradetool.baseAmount,'price':1000.0,'islimit':1,'cid':CIDtmp}
            tradetool.sendMsgToBitmexTrade('cs', msg)
        elif data == 'getalloride':
            tradetool.getAllTrade()
        elif data == 'cancelokex' or data == 'cokex':
            tradetool.cancelAllTrade('okex')
        elif data == 'cancelbitmex' or data == 'cbitmex':
            tradetool.cancelAllTrade('bitmex')
        elif data == 'getBitmexFunding':
            tradetool.getBitmexFunding()
        elif data == 'account':
            tradetool.getAccount()
        elif data == 'opentest' or data == 'ot':
            tradetool.setTradeTest(True)
        elif data == 'closetest' or data == 'ct':
            tradetool.setTradeTest(False)
        elif data == 'openlog' or data == 'olog':
            tradetool.setLogShow(True)
        elif data == 'closelog' or data == 'clog':
            tradetool.setLogShow(False)
        elif data == 'clear':
            tradetool.clearCache()
        elif data == 'print':
            tradetool.printDatas()
        elif data == 'start':
            tradetool.startDaly = 0
        elif data == 'stop':
            tradetool.startDaly = -1
        elif data == 't':
            print(tradetool.okexDatas[1][0])
        else:
            print(data)
    def setLogShow(self,isShowLog):

        if isShowLog:
            self.isShowLog = True
            print('open log')
        else:
            self.isShowLog = False
            print('close log')

    def initSocket(self):
        self.initOkexTradeSocket()
        self.initOkexDataSocket()
        self.initBitmexTradeSocket()
        self.initBitmexDataSocket()
    

    #获取Okex定单状态和数量
    def getOkexOrderList(self):
        pass

    #获取bitmex定单状态和数量
    def getBitmexOrderList(self):
        pass

    def initOkexTradeSocket(self):
        isErro = False
        try:
            print('connecting okex http trade server:',self.configdic['okex']['httpaddr'],self.configdic['okex']['httpport'])
            self.okexTradeSocket = socket.socket()  # instantiate
            self.okexTradeSocket.connect((self.configdic['okex']['httpaddr'], self.configdic['okex']['httpport']))  # connect to the server
            print('okex http trade server connected!')
            def okexTradeRun():
                while True:
                    data = self.okexTradeSocket.recv(100*1024)
                    isOK = False
                    try:
                        datadic = json.loads(data.decode())
                        isOK = True
                    except Exception as e:
                        print(data)
                        if len(data) == 0:
                            self.isOkexTradeOK = False
                            self.okexTradeSocket = None
                            return
                    if isOK:
                        self.onOkexTradeBack(datadic)
            self.okexTradethr = threading.Thread(target=okexTradeRun,args=())
            self.okexTradethr.setDaemon(True)
            self.okexTradethr.start()
            self.socketstate['ot'] = True
            self.isOkexTradeOK = True
        except Exception as e:
            print('connect okex http trade server erro...')
            self.okexTradeSocket = None
            isErro =  True
        return (not isErro)

    def initOkexDataSocket(self):
        isErro = False
        try:
            print('connecting okex ws data server:',self.configdic['okex']['wsaddr'],self.configdic['okex']['wsport'])
            self.okexDataSocket = socket.socket()  # instantiate
            self.okexDataSocket.connect((self.configdic['okex']['wsaddr'], self.configdic['okex']['wsport']))  # connect to the server
            print('okex ws data server connected!')
            def okexDataRun():
                while True:
                    data = self.okexDataSocket.recv(100*1024)
                    isDataOK = True
                    try:
                        datadic = json.loads(data.decode())
                    except Exception as e:
                        isDataOK = False
                        try:
                            if len(data) > 1:  #一次接收了多个json数据
                                datastr = data.decode()
                                if datastr.find('}{') != -1:
                                    datas = datastr.split('}{')
                                    if datas:
                                        for n in range(len(datas)):
                                            d = datas[n]
                                            if n == 0:
                                                dtmp = d + '}'
                                                dictmp = json.loads(dtmp)
                                                self.onOkexData(dictmp)
                                            elif n == len(datas) - 1:
                                                dtmp = '{' + d
                                                dictmp = json.loads(dtmp)
                                                self.onOkexData(dictmp)
                                            else:
                                                dtmp = '{' + d + '}'
                                                dictmp = json.loads(dtmp)
                                                self.onOkexData(dictmp)
                                    continue
                        except Exception as e2:
                            print(e2)

                    if isDataOK:
                        self.onOkexData(datadic)
                    else:
                        print(data)
                        if len(data) == 0:
                            self.okexDataSocket = None
                            self.isOkexDataOK = False
                            print('okexDataSocket erro')
                            return

            self.okexDatathr = threading.Thread(target=okexDataRun,args=())
            self.okexDatathr.setDaemon(True)
            self.okexDatathr.start()
            self.socketstate['od'] = True
        except Exception as e:
            print('connect erro okex ws data...')
            self.okexDataSocket = None
            isErro =  True
        return (not isErro)
    
    def initBitmexDataSocket(self):
        isErro = False
        try:
            print('connecting bitmex ws data server:',self.configdic['bitmex']['wsaddr'],self.configdic['bitmex']['wsport'])
            self.bitmexDataSocket = socket.socket()  # instantiate
            self.bitmexDataSocket.connect((self.configdic['bitmex']['wsaddr'], self.configdic['bitmex']['wsport']))  # connect to the server
            print('bitmex ws data server connected!')
            def bitmexDataRun():
                while True:
                    data = self.bitmexDataSocket.recv(100*1024)
                    isOKBitmexData = False
                    try:
                        datadic = json.loads(data.decode())
                        isOKBitmexData = True
                    except Exception as e:
                        print(data)
                        try:
                            if len(data) > 1:  #一次接收了多个json数据
                                datastr = data.decode()
                                if datastr.find('}{') != -1:
                                    datas = datastr.split('}{')
                                    if datas:
                                        for n in range(len(datas)):
                                            d = datas[n]
                                            if n == 0:
                                                dtmp = d + '}'
                                                dictmp = json.loads(dtmp)
                                                self.onBitmexData(dictmp)
                                            elif n == len(datas) - 1:
                                                dtmp = '{' + d
                                                dictmp = json.loads(dtmp)
                                                self.onBitmexData(dictmp)
                                            else:
                                                dtmp = '{' + d + '}'
                                                dictmp = json.loads(dtmp)
                                                self.onBitmexData(dictmp)
                                    continue
                        except Exception as e2:
                            print(e2)
                        
                    if isOKBitmexData:
                        self.onBitmexData(datadic)
                    else:
                        if len(data) == 0:
                            self.bitmexDataSocket = None
                            self.isBitmexDataOK = False
                            print('okexDataSocket erro')
                            return
                    
            self.bitmexDatathr = threading.Thread(target=bitmexDataRun,args=())
            self.bitmexDatathr.setDaemon(True)
            self.bitmexDatathr.start()
            self.socketstate['bd'] = True
        except Exception as e:
            print('connect erro bitmex ws data...')
            self.bitmexDataSocket = None
            isErro =  True
        return (not isErro)
    def initBitmexTradeSocket(self):
        isErro = False
        try:
            print('connecting bitmex Trade data server:',self.configdic['bitmex']['httpaddr'],self.configdic['bitmex']['httpport'])
            self.bitmexTradeSocket = socket.socket()  # instantiate
            self.bitmexTradeSocket.connect((self.configdic['bitmex']['httpaddr'], self.configdic['bitmex']['httpport']))  # connect to the server
            print('bitmex ws Trade server connected!')
            def okexDataRun():
                while True:
                    data = self.bitmexTradeSocket.recv(100*1024)
                    isOKBitmexTrade = False
                    try:
                        datadic = json.loads(data.decode())
                        isOKBitmexTrade = True
                    except Exception as e:
                        print(data)
                    if isOKBitmexTrade:
                        self.onBitmexTradeBack(datadic)
                    else:
                        if len(data) == 0:
                            self.bitmexTradeSocket = None
                            self.isBitmexTradeOK = False
            self.bitmexTradethr = threading.Thread(target=okexDataRun,args=())
            self.bitmexTradethr.setDaemon(True)
            self.bitmexTradethr.start()
            self.socketstate['bt'] = True
            self.isBitmexTradeOK = True
        except Exception as e:
            print('connect erro bitmex trade...')
            self.bitmexTradeSocket = None
            isErro =  True
        return (not isErro)


    def timeconvent(self,utcstrtime):
        timest = timetool.utcStrTimeToTime(utcstrtime)
        timeint = int(timest)
        ltimeStr = str(timetool.timestamp2datetime(timeint,True))   
        return timeint,ltimeStr 

    def saveSubData(self):
        smsg = 'ob:%.2f,%d,%d,bo:%.2f,%d,%d,%d,%d'%(round(self.lastSub['ob']['subOB'],3),self.lastSub['ob']['odeep'],self.lastSub['ob']['bdeep'],round(self.lastSub['bo']['subBO'],3),self.lastSub['bo']['odeep'],self.lastSub['bo']['bdeep'],self.lastSub['subtime'],int(time.time()))
        smsg += '|bmex:(%.2f,%.2f),okex:(%.2f,%.2f)\n'%(self.bitmexDatas[0][0],self.bitmexDatas[1][0],self.okexDatas[0][0],self.okexDatas[1][0])
        f = open(self.subsavefilename,'a')
        f.write(smsg)
        f.close()
    def updateDataSub(self):
        #self.okexDatas = []             #买一价，卖一价，接收数据时间
        #self.bitmexDatas = []           #买一价，卖一价, 接收数据时间
        #self.lastSub = []               #okex的卖一价和bitmex的买一价的差价，bitmex的卖一价和okex的买一价的差价,时间差,最后接收时间
        if self.okexDatas and self.bitmexDatas:
            # priceOBSellSub = self.okexDatas[1][0] - self.bitmexDatas[1][0]
            # priceOBBuySub = self.okexDatas[0][0] - self.bitmexDatas[0][0]
        
            # self.lastSub['ob'] = {'subOB':self.okexDatas[1][0] - self.bitmexDatas[0][0],'odeep':self.okexDatas[1][1],'bdeep':self.bitmexDatas[0][1]}
            # self.lastSub['bo'] = {'subBO':self.bitmexDatas[1][0] - self.okexDatas[0][0],'odeep':self.okexDatas[0][1],'bdeep':self.bitmexDatas[1][1]}
            self.lastSub['ob'] = {'subOB':self.okexDatas[0][0] - self.bitmexDatas[0][0],'odeep':self.okexDatas[0][1],'bdeep':self.bitmexDatas[0][1]}
            self.lastSub['bo'] = {'subBO':self.okexDatas[1][0] - self.bitmexDatas[1][0],'odeep':self.okexDatas[1][1],'bdeep':self.bitmexDatas[1][1]}
            
            self.lastSub['otime'] = self.okexDatas[2]
            self.lastSub['btime'] = self.bitmexDatas[2]
            self.lastSub['subtime'] = self.okexDatas[2] - self.bitmexDatas[2]
            # print('-'*20)
            if self.isShowLog:
                # print('ob:',round(self.lastSub['ob']['subOB'],3),self.lastSub['ob']['odeep'],self.lastSub['ob']['bdeep'],'bo:',round(self.lastSub['bo']['subBO'],3),self.lastSub['bo']['odeep'],self.lastSub['bo']['bdeep'],self.lastSub['subtime'])
                pricelog0 = 'ob:%.2f,%d,%d,bo:%.2f,%d,%d,%d'%(round(self.lastSub['ob']['subOB'],3),self.lastSub['ob']['odeep'],self.lastSub['ob']['bdeep'],round(self.lastSub['bo']['subBO'],3),self.lastSub['bo']['odeep'],self.lastSub['bo']['bdeep'],self.lastSub['subtime'])
                lenstrcount = len(pricelog0)
                if lenstrcount > self.maxStrlen:
                    self.maxStrlen = lenstrcount
                pricelog0 = pricelog0.ljust(self.maxStrlen, ' ')
                pricelog = 'bmex:(%.2f,%.2f) | okex:(%.2f,%.2f)'%(self.bitmexDatas[0][0],self.bitmexDatas[1][0],self.okexDatas[0][0],self.okexDatas[1][0])
                # print(pricelog)
                self.priceWinlog = [pricelog,pricelog0]
            self.tradeTest()
            # self.saveSubData()
    #初始化交易参数,如单次下单合约值，谁主动成交，谁被动成交,交易手续费等
    def initTraddeConfig(self,conf):
        self.tradeConfig = conf
        self.iOkexRate = self.tradeConfig['iOkexRate']
        self.pOkexRate = self.tradeConfig['pOkexRate']
        self.iBiemexRate = self.tradeConfig['iBiemexRate']
        self.pBiemexRate = self.tradeConfig['pBiemexRate']
        # self.stepPercent = self.tradeConfig['stepPercent']
        self.stepPercent = (self.iOkexRate + self.iBiemexRate)*conf['stepPercent']
        # self.movePercent = self.tradeConfig['movePercent']
        self.movePercent = self.stepPercent*conf['movePercent']
        self.normTime = self.tradeConfig['normTime']*60*60    #小时换算成秒
        self.baseAmount = self.tradeConfig['baseAmount']      #okex合约张数，bitmex要X100
        self.startDaly = self.tradeConfig['startDaly']
        if self.isInitOnce:  #只在启动时初始化一次的数据,在作来自动改变更新的配置
            self.baseOB = self.tradeConfig['baseOB']             #初始OB仓位
            self.baseBO = self.tradeConfig['baseBO']             #初始BO仓位
            self.isInitOnce = False
        self.basePrice = self.tradeConfig['basePrice']
        self.autoBase = self.tradeConfig['autoBase'] 
        self.dalyPrice = self.tradeConfig['dalyPrice'] 

    #生成用户自定义定单ID
    def crecteOrderCID(self,orderType):
        # self.bCIDBase = 0               #bitmex的用户自定义定单ID基数
        cid = ''
        if orderType == 'oob':
            self.obCount += 1
            cid = orderType + '-' + str(self.obCount) + '-' + str(int(time.time()))
        elif orderType == 'obo':
            self.boCount += 1
            cid = orderType + '-' + str(self.boCount) + '-' + str(int(time.time()))
        elif orderType == 'cob':
            cid = orderType + '-' + str(self.obCount) + '-' + str(int(time.time()))
            self.obCount -= 1
        elif orderType == 'cbo':
            cid = orderType + '-' + str(self.boCount) + '-' + str(int(time.time()))
            self.boCount -= 1
        elif orderType == 'coba':
            cid = orderType + '-' + str(self.obCount) + '-' + str(int(time.time()))
            self.obCount = 0
        elif orderType == 'cboa':
            cid = orderType + '-' + str(self.boCount) + '-' + str(int(time.time()))
            self.boCount = 0
        else:
            self.bCIDBase += 1
            cid = orderType + '-' + str(self.bCIDBase) + '-' + str(int(time.time()))
        return cid

    def openOB(self,subpurce,isReset = False): #开仓,okex买入，bitmex卖出
        cid = self.crecteOrderCID('oob')
        msg = {'type':'os','amount':self.baseAmount*100,'price':self.bitmexDatas[1][0],'islimit':1,'cid':cid}
        self.bCIDData[cid] = {'msg':msg,'state':0,'type':'oob','subprice':subpurce,'sub':[]}
        self.tradeState = 121 #121.bitmex开空正在下单
        smsg = '开仓OB,bitmex价格为%.1f'%(self.bitmexDatas[1][0])
        sayMsg(smsg)
        if self.bitmexTradeStartTime == 0:
            self.bitmexTradeStartTime = int(time.time())
        if self.sendMsgToBitmexTrade('os', msg):
            self.nowTradeCID = cid
            # self.tradeState = 122 #5.bitmex开空下单已发送，等成交
            self.lastBitmexTradeTime = int(time.time())
            # self.lastOkexTradeTime = 0
            self.okexTradeMsgs.append({'type':'ol','amount':self.baseAmount,'cid':cid})
            if isReset:
                self.obsubs.pop()
                self.obsubs.append(self.bitmexDatas[1][0]-self.okexDatas[1][0])
            else:
                self.obsubs.append(self.bitmexDatas[1][0]-self.okexDatas[1][0])
            print(self.obsubs)
            return msg
        return None
        
        
    def closeOB(self,subpurce,closeAll = False,isReset = False):#平仓,okex卖出，bitmex买入
        if closeAll:
            pp = len(self.obsubs) + self.baseOB
            cid = self.crecteOrderCID('coba')
            msg = {'type':'cs','amount':self.baseAmount*100*pp,'price':self.bitmexDatas[0][0],'islimit':1,'cid':cid}
            self.bCIDData[cid] = {'msg':msg,'state':0,'type':'coba','subprice':subpurce,'sub':[]}
            self.tradeState = 141 #141.bitmex平空正在下单
            smsg = '所有OB平仓,bitmex价格为%.1f'%(self.bitmexDatas[0][0])
            sayMsg(smsg)
            if self.bitmexTradeStartTime == 0:
                self.bitmexTradeStartTime = int(time.time())
            if self.sendMsgToBitmexTrade('cs', msg):
                self.nowTradeCID = cid
                # self.tradeState = 142 #11.bitmex平空下单已发送，等成交
                self.lastBitmexTradeTime = int(time.time())
                # self.lastOkexTradeTime = 0
                self.okexTradeMsgs.append({'type':'cl','amount':self.baseAmount*pp,'cid':cid})
                self.bCIDData[cid]['sub'] = list(self.obsubs)
                self.obsubs = []
                return msg
        else:
            cid = self.crecteOrderCID('cob')
            msg = {'type':'cs','amount':self.baseAmount*100,'price':self.bitmexDatas[0][0],'islimit':1,'cid':cid}
            self.bCIDData[cid] = {'msg':msg,'state':0,'type':'cob','subprice':subpurce,'sub':[]}
            self.tradeState = 141 #141.bitmex平空正在下单
            smsg = '平仓OB,bitmex价格为%.1f'%(self.bitmexDatas[0][0])
            sayMsg(smsg)
            if self.bitmexTradeStartTime == 0:
                self.bitmexTradeStartTime = int(time.time())
            if self.sendMsgToBitmexTrade('cs', msg):
                self.nowTradeCID = cid
                # self.tradeState = 142 #142.bitmex平空下单已发送，等成交
                self.lastBitmexTradeTime = int(time.time())
                self.okexTradeMsgs.append({'type':'cl','amount':self.baseAmount,'cid':cid})
                if not isReset:
                    if self.obsubs:
                        subprice = self.obsubs.pop()
                        self.bCIDData[cid]['sub'] = [subprice]
                    else:
                        self.isCloseBaseOB = True
                return msg
            print(self.obsubs)
        return None
        

    def openBO(self,subpurce,isReset = False): #开仓,bitmex买入,okex卖出
        cid = self.crecteOrderCID('obo')
        msg = {'type':'ol','amount':self.baseAmount*100,'price':self.bitmexDatas[0][0],'islimit':1,'cid':cid}
        self.bCIDData[cid] = {'msg':msg,'state':0,'type':'obo','subprice':subpurce,'sub':[]}
        self.tradeState = 111 #111.bitmex开多正在下单
        smsg = '开仓BO,bitmex价格为%.1f'%(self.bitmexDatas[0][0])
        sayMsg(smsg)
        if self.bitmexTradeStartTime == 0:
                self.bitmexTradeStartTime = int(time.time())
        if self.sendMsgToBitmexTrade('ol', msg):
            self.nowTradeCID = cid
            # self.tradeState = 112 #112.bitmex开多下单已发送，等成交
            self.lastBitmexTradeTime = int(time.time())
            self.okexTradeMsgs.append({'type':'os','amount':self.baseAmount,'cid':cid})
            if isReset:
                self.bosubs.pop()
                self.bosubs.append(self.bitmexDatas[0][1]-self.okexDatas[0][0])
            else:
                self.bosubs.append(self.bitmexDatas[0][1]-self.okexDatas[0][0])
            print(self.bosubs)
            return msg
        return None

    def closeBO(self,subpurce,closeAll = False,isReset = False):#平仓,bitmex卖出,okex买入
        if closeAll:
            pp =len(self.bosubs) + self.baseBO
            cid = self.crecteOrderCID('cboa')
            msg = {'type':'cl','amount':self.baseAmount*100*pp,'price':self.bitmexDatas[0][0],'islimit':1,'cid':cid}
            self.bCIDData[cid] = {'msg':msg,'state':0,'type':'cboa','subprice':subpurce,'sub':[]}
            self.tradeState = 131 #131.bitmex平多正在下单
            smsg = '所有BO平仓,bitmex价格为%.1f'%(self.bitmexDatas[0][0])
            sayMsg(smsg)
            if self.bitmexTradeStartTime == 0:
                self.bitmexTradeStartTime = int(time.time())
            if self.sendMsgToBitmexTrade('cl', msg):
                self.nowTradeCID = cid
                # self.tradeState = 132 #132.bitmex平多下单已发送，等成交
                self.lastBitmexTradeTime = int(time.time())
                self.okexTradeMsgs.append({'type':'cs','amount':self.baseAmount*pp,'cid':cid})
                self.bCIDData[cid]['sub'] = list(self.bosubs)
                self.bosubs = []
                return msg
        else:
            cid = self.crecteOrderCID('cbo')
            msg = {'type':'cl','amount':self.baseAmount*100,'price':self.bitmexDatas[0][0],'islimit':1,'cid':cid}
            self.bCIDData[cid] = {'msg':msg,'state':0,'type':'cbo','subprice':subpurce,'sub':[]}
            self.tradeState = 131 #131.bitmex平多正在下单
            smsg = '平仓BO,bitmex价格为%.1f'%(self.bitmexDatas[0][0])
            sayMsg(smsg)
            if self.bitmexTradeStartTime == 0:
                self.bitmexTradeStartTime = int(time.time())
            if self.sendMsgToBitmexTrade('cl', msg):
                self.nowTradeCID = cid
                # self.tradeState = 132 #132.bitmex平多下单已发送，等成交
                self.lastBitmexTradeTime = int(time.time())
                self.okexTradeMsgs.append({'type':'cs','amount':self.baseAmount,'cid':cid})
                if not isReset:
                    if self.bosubs:
                        subprice = self.bosubs.pop()
                        self.bCIDData[cid]['sub'] = [subprice]
                    else:
                        self.isCloseBaseBO = True
                print(self.bosubs)
                return msg
        return None

    def clearCache(self):
        self.obsubs = []
        self.bosubs = []
        self.okexTradeMsgs = []
        self.bCIDData = {}
        self.oCIDData = {}
        print('clear:obsubs,bosubs,okexTradeMsgs,bCIDData,oCIDData')

    def printDatas(self):
        print('---------okexTradeMsgs------------')
        print(self.okexTradeMsgs)
        print('---------bCIDData------------')
        print(self.bCIDData)
        print('----------oCIDData-----------')
        print(self.oCIDData)
        print('---------obsubs------------')
        print(self.obsubs)
        print('----------bosubs-----------')
        print(self.bosubs)
        

    #检测是否需要下单
    def tradeTest(self):
        isStop = False

        if self.startDaly < 0:
            isStop = True
        elif self.startDaly > 0:
            ntime = (int(time.time()) - self.toolStartTime)/60
            if ntime < self.startDaly:#未达到开始时间
                isStop = True

        if not (self.isBitmexDataOK and self.isOkexDataOK):
            #数据接收服务器是否出错，不论好一个出错，都不能进行下单交易
            showlog = '数据服务器未准备好，bitmex:%d,okex:%d'%(self.isBitmexDataOK,self.isOkexDataOK)
            print(showlog.encode())
            isStop = True

        if not (self.isBitmexTradeOK and self.isOkexTradeOK):
            showlog = '下单服务器未准备好，bitmex:%d,okex:%d'%(self.isBitmexTradeOK,self.isOkexTradeOK)
            print(showlog.encode())
            isStop = True

        

        ptime = int(time.time())
        if ptime - self.lastBitmexTradeTime < 3 or ptime - self.lastOkexTradeTime < 3:
            #防止出现快速连续下单情况,每一次下新交易对，必须等3秒以上才可以下新单
            print('time ...')
            isStop = True


        lastOBsub = self.lastSub['ob']['subOB'] - self.basePrice
        priceOBSellSub = self.okexDatas[1][0] - self.bitmexDatas[1][0]
        priceOBBuySub = self.okexDatas[0][0] - self.bitmexDatas[0][0]
        
        if self.tradeState != 0 and (not isStop):
            maxprice = 0
            stepprice = 0
            tmpprice = 0
            if lastOBsub <= 0:
                maxprice = self.bitmexDatas[1][0]
                stepprice = maxprice * self.stepPercent
                tmpprice = -(self.tradecount)*stepprice
            else:
                maxprice = self.okexDatas[1][0]
                stepprice = maxprice * self.stepPercent
                tmpprice = (self.tradecount)*stepprice
            
            if self.nowTradeCID != '':
                isNotCtest = True
                # delyprice = 2

                tmplogstr = 'tradestate:%d'%(self.tradeState)
                print(tmplogstr)
                # if self.bitmexTradeStartTime > 100 and ptime - self.bitmexTradeStartTime > 30 and self.tradeState < 200 and self.tradeState%10 == 1:
                #     print('bitmex下单错误,服务器30秒内未回应,bitmex下单失败')
                #     if self.nowTradeCID != '':
                #     self.bitmexTradeStartTime = 0

                if self.tradeState == 112: #bitmex开多正在等成交
                    print('bitmex开多正在等成交'.encode())
                    # msg = {'type':'cl','amount':self.baseAmount*100,'price':self.bitmexDatas[0][0],'islimit':1,'cid':cid}
                    # self.bCIDData[cid] = {'msg':msg,'state':0,'type':'cbo','subprice':subpurce,'sub':[]}
                    print(self.bCIDData[self.nowTradeCID]['subprice'],priceOBBuySub + self.dalyPrice,self.bCIDData[self.nowTradeCID]['msg']['price'],self.bitmexDatas[0][0])
                        
                    if self.bCIDData[self.nowTradeCID]['subprice'] > priceOBBuySub + self.dalyPrice or self.bitmexDatas[0][0] - self.bCIDData[self.nowTradeCID]['msg']['price'] >= 10:
                        #当下单条件不存在了，或者下单价差别比较大时，取消下单
                        
                        # print(self.bCIDData[self.nowTradeCID]['subprice'],tmpprice-2,self.bCIDData[self.nowTradeCID]['msg']['price'],self.bitmexDatas[0][0])
                        if isNotCtest:
                            self.tradeState = 113
                            self.cancelOneTrade('bitmex', self.nowTradeCID)
                        # sayMsg('bitmex开多要取消')
                elif self.tradeState == 122: #bitmex开空正在等成交
                    print('bitmex开空正在等成交'.encode())
                    print(self.bCIDData[self.nowTradeCID]['subprice'],priceOBSellSub - self.dalyPrice,self.bCIDData[self.nowTradeCID]['msg']['price'],self.bitmexDatas[1][0])
                        
                    if self.bCIDData[self.nowTradeCID]['subprice'] < priceOBSellSub - self.dalyPrice  or self.bCIDData[self.nowTradeCID]['msg']['price'] - self.bitmexDatas[1][0] >= 10:
                        #当下单条件不存在了，或者下单价差别比较大时，取消下单
                        # (-127.27000000000001, -125.27000000000001, 6363.5, 6363.5)
                        # print(self.bCIDData[self.nowTradeCID]['subprice'],tmpprice+2,self.bCIDData[self.nowTradeCID]['msg']['price'],self.bitmexDatas[1][0])
                        if isNotCtest:
                            self.tradeState = 123
                            self.cancelOneTrade('bitmex', self.nowTradeCID)
                        # sayMsg('bitmex开空要取消')
                elif self.tradeState == 132: #bitmex平多正在等成交
                    print('bitmex平多正在等成交'.encode())
                    print(self.bCIDData[self.nowTradeCID]['subprice'],priceOBSellSub -self.dalyPrice ,self.bCIDData[self.nowTradeCID]['msg']['price'],self.bitmexDatas[1][0])
                       
                    if self.bCIDData[self.nowTradeCID]['type'] == 'cboa' and (self.bCIDData[self.nowTradeCID]['subprice'] < priceOBSellSub -self.dalyPrice or self.bCIDData[self.nowTradeCID]['msg']['price'] - self.bitmexDatas[1][0] >= 10):
                        # print(self.bCIDData[self.nowTradeCID]['subprice'],lastOBsub + 2,self.bCIDData[self.nowTradeCID]['msg']['price'],self.bitmexDatas[1][0])
                       
                        if isNotCtest:
                            self.tradeState = 133
                            self.cancelOneTrade('bitmex', self.nowTradeCID)
                        # sayMsg('bitmex所有平多要取消')
                    elif self.bCIDData[self.nowTradeCID]['subprice'] < priceOBSellSub -self.dalyPrice or self.bCIDData[self.nowTradeCID]['msg']['price'] - self.bitmexDatas[1][0] >= 10:
                        #当下单条件不存在了，或者下单价差别比较大时，取消下单
                        # print(self.bCIDData[self.nowTradeCID]['subprice'],tmpprice + 2 ,self.bCIDData[self.nowTradeCID]['msg']['price'],self.bitmexDatas[1][0])
                       
                        if isNotCtest:
                            self.tradeState = 133
                            self.cancelOneTrade('bitmex', self.nowTradeCID)
                        # sayMsg('bitmex平多要取消')
                elif self.tradeState == 142: #bitmex平空正在等成交
                    print('bitmex平空正在等成交'.encode())
                    print(self.bCIDData[self.nowTradeCID]['subprice'],priceOBBuySub + self.dalyPrice ,self.bCIDData[self.nowTradeCID]['msg']['price'],self.bitmexDatas[0][0])
                       
                    if self.bCIDData[self.nowTradeCID]['type'] == 'coba' and (self.bCIDData[self.nowTradeCID]['subprice'] > priceOBBuySub + self.dalyPrice or self.bitmexDatas[0][0] - self.bCIDData[self.nowTradeCID]['msg']['price'] >= 10):
                        # print(self.bCIDData[self.nowTradeCID]['subprice'],tmpprice - 2 ,self.bCIDData[self.nowTradeCID]['msg']['price'],self.bitmexDatas[0][0])
                       
                        if isNotCtest:
                            self.tradeState = 143
                            self.cancelOneTrade('bitmex', self.nowTradeCID)
                        # sayMsg('bitmex所有平空要取消')
                    elif self.bCIDData[self.nowTradeCID]['subprice'] > priceOBBuySub +self.dalyPrice or self.bitmexDatas[0][0] - self.bCIDData[self.nowTradeCID]['msg']['price'] >= 10:
                        #当下单条件不存在了，或者下单价差别比较大时，取消下单
                        # print(self.bCIDData[self.nowTradeCID]['subprice'],tmpprice - 2 ,self.bCIDData[self.nowTradeCID]['msg']['price'],self.bitmexDatas[0][0])
                       
                        if isNotCtest:
                            self.tradeState = 143
                            self.cancelOneTrade('bitmex', self.nowTradeCID)
                        # sayMsg('bitmex平空要取消')
                elif self.tradeState == 212: #okex开多正在等成交
                    print('okex开多正在等成交'.encode())
                    print(self.okexDatas[0][0],self.oCIDData[self.nowTradeCID]['msg']['price'])
                    # msg = {'type':'cl','amount':datadic['data']['amount'],'price':self.okexDatas[0][0]-5,'islimit':1,'cid':datadic['data']['cid']}
                    # self.oCIDData[datadic['cid']] = {'msg':msg,'state':0,'cid':datadic['cid']}
                    if self.okexDatas[0][0] - self.oCIDData[self.nowTradeCID]['msg']['price'] > 3:
                        # print(self.okexDatas[0][0],self.oCIDData[self.nowTradeCID]['msg']['price'])
                        if isNotCtest:
                            self.tradeState = 213
                            self.cancelOneTrade('okex', self.okexOIDDic[self.nowTradeCID])
                        # sayMsg('okex开多要取消')
                elif self.tradeState == 222: #okex开空正在等成交
                    print('okex开空正在等成交'.encode())
                    print(self.okexDatas[1][0],self.oCIDData[self.nowTradeCID]['msg']['price'])
                    if self.oCIDData[self.nowTradeCID]['msg']['price'] - self.okexDatas[1][0]  > 3:
                        # print(self.okexDatas[1][0],self.oCIDData[self.nowTradeCID]['msg']['price'])
                        if isNotCtest:
                            self.tradeState = 223
                            self.cancelOneTrade('okex', self.okexOIDDic[self.nowTradeCID])
                        # sayMsg('okex开空要取消')
                elif self.tradeState == 232: #okex平多正在等成交
                    print('okex平多正在等成交'.encode())
                    print(self.okexDatas[1][0],self.oCIDData[self.nowTradeCID]['msg']['price'])
                    if self.oCIDData[self.nowTradeCID]['msg']['price'] - self.okexDatas[1][0]  > 3:
                        # print(self.okexDatas[1][0],self.oCIDData[self.nowTradeCID]['msg']['price'])
                        if isNotCtest:
                            self.tradeState = 223
                            self.cancelOneTrade('okex', self.okexOIDDic[self.nowTradeCID])
                        # sayMsg('okex平多要取消')
                elif self.tradeState == 242: #okex平空正在等成交
                    print('okex平空正在等成交'.encode())
                    print(self.okexDatas[0][0],self.oCIDData[self.nowTradeCID]['msg']['price'])
                    if self.okexDatas[0][0] - self.oCIDData[self.nowTradeCID]['msg']['price'] > 3:
                        # print(self.okexDatas[0][0],self.oCIDData[self.nowTradeCID]['msg']['price'])
                        if isNotCtest:
                            self.tradeState = 213
                            self.cancelOneTrade('okex', self.okexOIDDic[self.nowTradeCID])
                        # sayMsg('okex平空要取消')
                print('\n')
            isStop = True

        # self.showLogCount -= 1

        # if self.showLogCount < 0:
        #     self.showLogCount = 10
        
        if lastOBsub <= 0:  #bitmex价格高于okex
            maxprice = self.bitmexDatas[1][0]
            stepprice = maxprice * self.stepPercent
            if self.isShowLog and isStop:
                tmplog2 = 'stepprice=%.2f,%d'%(stepprice,isStop)
                self.priceWinlog.insert(-2,tmplog2)

            if isStop:
                showlogtmp = ' | '.join(self.priceWinlog)
                showlogtmp = '\r' + showlogtmp
                self.sendMsgToClient(showlogtmp[1:])
                sys.stdout.writelines(showlogtmp)
                sys.stdout.flush()
                # print('ddd')
                self.priceWinlog = []
                return
            if len(self.bosubs) > 1:
                self.closeBO(priceOBSellSub,closeAll = True)
            elif abs(lastOBsub/stepprice) > 0.0:
                c = abs((lastOBsub+2)/stepprice) - len(self.obsubs) - self.baseOB
                self.tradecount = len(self.obsubs) + self.baseOB + 1
                tmpprice = -(self.tradecount)*stepprice
                psmallprice = tmpprice + self.basePrice
                pbigprice = tmpprice + 2*stepprice + self.basePrice
                if self.showLogCount == 0:
                    tmpstr = 'last<0,sub:%.2f,%d,%.3f,%d,m:%.2f,s:%.2f,%.2f'%(self.lastSub['ob']['subOB'],len(self.obsubs),c,self.baseOB,tmpprice + 2*stepprice + self.basePrice,tmpprice + self.basePrice,stepprice)
                    # tmpstr = '\r' + tmpstr
                    if self.priceWinlog:
                        self.priceWinlog.insert(-2, tmpstr)
                        tmpstr = '\r' + ' | '.join(self.priceWinlog)
                    else:
                        tmpstr = '\r' + tmpstr
                    self.sendMsgToClient(tmpstr[1:])
                    sys.stdout.writelines(tmpstr)
                    # print('\r',str(10-i).ljust(10),end='') #python 3使用的方法
                    # print('\r',tmpstr.ljust(100))
                    sys.stdout.flush()
                    self.priceWinlog = []
                if self.lastSub['ob']['subOB'] < psmallprice:
                    # opencount = math.floor(c)
                    self.openOB(priceOBSellSub)
                elif self.lastSub['ob']['subOB'] > pbigprice:
                    self.closeOB(priceOBBuySub)
            else:
                print('other.1..')
                
        elif lastOBsub > 0:
            maxprice = self.okexDatas[1][0]
            stepprice = maxprice * self.stepPercent
            if self.isShowLog and isStop:
                # print('stepprice=%.2f,%d'%(stepprice,isStop))
                tmplog2 = 'stepprice=%.2f,%d'%(stepprice,isStop)
                self.priceWinlog.insert(-2,tmplog2)
            if isStop:
                showlogtmp = ' | '.join(self.priceWinlog)
                showlogtmp = '\r' + showlogtmp
                self.sendMsgToClient(showlogtmp[1:])
                sys.stdout.writelines(showlogtmp)
                sys.stdout.flush()
                # print('ddd')
                self.priceWinlog = []
                return

            if len(self.obsubs) > 1:
                self.closeOB(priceOBBuySub,closeAll = True)
            elif abs(lastOBsub/stepprice) > 0.0:
                c =  abs((lastOBsub-2)/stepprice) - len(self.bosubs) - self.baseBO
                self.tradecount = len(self.bosubs) + self.baseBO + 1
                tmpprice = (self.tradecount)*stepprice
                psmallprice = tmpprice - 2*stepprice + self.basePrice
                pbigprice = tmpprice + self.basePrice
                if self.showLogCount == 0:
                    tmpstr = 'last>0,sub:%.2f,%d,%.3f,%d,m:%.2f,s:%.2f,%.2f'%(self.lastSub['ob']['subOB'],len(self.bosubs),c,self.baseOB,tmpprice + self.basePrice,tmpprice - 2*stepprice + self.basePrice,stepprice)
                    # print(tmpstr)
                    if self.priceWinlog:
                        self.priceWinlog.insert(-2, tmpstr)
                        tmpstr = '\r' + ' | '.join(self.priceWinlog)
                    else:
                        tmpstr = '\r' + tmpstr
                    self.sendMsgToClient(tmpstr[1:])
                    sys.stdout.writelines(tmpstr)
                    # print('\r',str(10-i).ljust(10),end='') #python 3使用的方法
                    # print('\r',tmpstr.ljust(100))
                    sys.stdout.flush()
                    self.priceWinlog = []
                if self.lastSub['ob']['subOB'] > pbigprice:
                    # opencount = math.floor(c)
                    self.openBO(priceOBBuySub)
                elif self.lastSub['ob']['subOB'] < psmallprice:
                    self.closeBO(priceOBSellSub)
                # if c < 1.0:
                #     opencount = math.floor(c)
                #     self.openBO(priceOBBuySub)
                # elif c < -1:
                #     self.closeBO(priceOBSellSub)
            else:
                print('other.2..')
                


        # lastOBsub = self.lastSub['ob']['subOB']
        # lastBOsub = self.lastSub['bo']['subBO']
        # if lastOBsub <= 0:  #bitmex价格高于okex
        #     maxprice = self.bitmexDatas[1][0]
        #     stepprice = maxprice * self.stepPercent
        #     if self.isShowLog:
        #         print('stepprice=%.2f'%(stepprice))
        #     if isStop:
        #         return
        #     if len(self.obsubs) < 1:
        #         if abs(lastOBsub) > stepprice and len(self.obsubs) < 1:
        #             self.openOB(stepprice)
        #         elif abs(lastOBsub) > stepprice*((1+self.stepPercent)^2) and len(self.obsubs) < 2:
        #             self.openOB(stepprice*((1+self.stepPercent)^2))
        #         elif abs(lastOBsub) > stepprice*((1+self.stepPercent)^3) and len(self.obsubs) < 3:
        #             self.openOB(stepprice*((1+self.stepPercent)^3))
        #         elif abs(lastOBsub) > stepprice*((1+self.stepPercent)^4) and len(self.obsubs) < 4:
        #             self.openOB(stepprice*((1+self.stepPercent)^4))
        #         elif abs(lastOBsub) > stepprice*((1+self.stepPercent)^5) and len(self.obsubs) < 5:
        #             self.openOB(stepprice*((1+self.stepPercent)^5))
        #         elif abs(lastOBsub) > stepprice*((1+self.stepPercent)^6) and len(self.obsubs) < 6:
        #             self.openOB(stepprice*((1+self.stepPercent)^6))
        #     elif abs(lastOBsub) > stepprice and len(self.bosubs) > 0:
        #         self.closeBO(stepprice,closeAll = True)
        # elif lastBOsub < 0:
        #     maxprice = self.okexDatas[1][0]
        #     stepprice = maxprice * self.stepPercent
        #     if self.isShowLog:
        #         print('stepprice=%.2f'%(stepprice))
        #     if isStop:
        #         return
        #     if len(self.obsubs) < 1:
        #         if abs(lastBOsub) > stepprice and len(self.obsubs) < 1:
        #             self.openBO(stepprice)
        #         elif abs(lastBOsub) > stepprice*((1+self.stepPercent)^2) and len(self.obsubs) < 2:
        #             self.openBO(stepprice*((1+self.stepPercent)^2))
        #         elif abs(lastBOsub) > stepprice*((1+self.stepPercent)^3) and len(self.obsubs) < 3:
        #             self.openBO(stepprice*((1+self.stepPercent)^3))
        #         elif abs(lastBOsub) > stepprice*((1+self.stepPercent)^4) and len(self.obsubs) < 4:
        #             self.openBO(stepprice*((1+self.stepPercent)^4))
        #         elif abs(lastBOsub) > stepprice*((1+self.stepPercent)^5) and len(self.obsubs) < 5:
        #             self.openBO(stepprice*((1+self.stepPercent)^5))
        #         elif abs(lastBOsub) > stepprice*((1+self.stepPercent)^6) and len(self.obsubs) < 6:
        #             self.openBO(stepprice*((1+self.stepPercent)^6))
        #     elif abs(lastBOsub) > stepprice and len(self.bosubs) > 0:
        #         self.closeOB(stepprice,closeAll = True)

        # "iOkexRate":0.0005,     //okex主动成交费率
        # "pOkexRate":0.0002,     //okex被动成交费率
        # "iBiemexRate":0.00075,  //bitmex主动成交费率
        # "pBiemexRate":-0.00025,   //bitmex被动成交费率
        # "stepPercent":0.005,    //下单网格价格百分比大小
        # "movePercent":0.003,    //网格滑动价格百分比
        # "normTime":3,           //基准价格重新计算时间,单位:小时
        # "reconfigTime":60       //配置文件检测刷新时间，单位:秒
    


    # 下单数据格式:
    # 开多,
    # {type:ol,amount:100,price:100,islimit:1}
    # 平多,
    # {type:cl,amount:100,price:100,islimit:1}
    # 开空,
    # {type:os,amount:100,price:100,islimit:1}
    # 平空
    # {type:cs,amount:100,price:100,islimit:1}

    # 获取定单状态
    # 获取所有定单状态
    # {type:getall}
    def getAllTrade(self,market = 'all'):
        msg = {'type':'getall'}
        if market == 'all':
            self.sendMsgToOkexTrade('getall', msg)
            self.sendMsgToBitmexTrade('getall', msg)
        elif market == 'okex':
            self.sendMsgToOkexTrade('getall', msg)
        elif market == 'bitmex':
            self.sendMsgToBitmexTrade('getall', msg)
    # 使用定单ID获取定单状态
    # {type:getID,id:123456}
    def getTrade(self,market,orderID):
        msg = {'type':'getID','id':orderID}
        if market == 'okex':
            self.sendMsgToOkexTrade('getID', msg)
        elif market == 'bitmex':
            self.sendMsgToBitmexTrade('getID', msg)
    
    # 取消所有定单
    # {type:cancelall}
    def cancelAllTrade(self,market):
        msg = {'type':'cancelall'}
        lastBiemexState = self.tradeState
        if market == 'all':
            self.sendMsgToOkexTrade('cancelall', msg)
            self.tradeState = 3 #3.bitmex开多正在取消下单,这里的数值只认为正在取消定单，不一定是开多定单
            if not self.sendMsgToBitmexTrade('cancelall', msg):
                self.tradeState = lastBiemexState
        elif market == 'okex':
            self.tradeState = 16 #16.okex开多正在取消定单，这里的数值只认为正在取消定单，不一定是开多定单
            if not self.sendMsgToOkexTrade('cancelall', msg):
                self.tradeState = lastBiemexState
        elif market == 'bitmex':
            self.tradeState = 3 #3.bitmex开多正在取消下单,这里的数值只认为正在取消定单，不一定是开多定单
            if not self.sendMsgToBitmexTrade('cancelall', msg):
                self.tradeState = lastBiemexState
    # 获取费率
    # {type:funding}
    def getBitmexFunding(self):
        msg = {'type':'funding'}
        self.sendMsgToBitmexTrade('funding', msg)
    
    # 帐户
    # 获取帐户信息
    # {type:account}
    def getAccount(self):
        msg = {'type':'account'}
        self.sendMsgToOkexTrade('account', msg)
        self.sendMsgToBitmexTrade('account', msg)
    # 提现
    # {type:withdraw,addr:地址,amount:数量,price:支付手续费,cointype:btc}
    # okex资金划转
    # {type:transfer,amount:数量,from:从那个资金帐户划转,to:划转到那个资金帐户,cointype:btc}
    def setTradeTest(self,isTest):
        msg = {'type':'test','test':isTest}
        self.sendMsgToOkexTrade('test', msg)
        self.sendMsgToBitmexTrade('test', msg)
    #收到数据   
    #okex数据

    def onOkexData(self,datadic):
        isOkexRun = True
        if 'type' in datadic:
            if datadic['type'] == 'pong':
                self.socketstate['od'] = True
                # print('pong from okex ws data server...')
            elif datadic['type'] == 'socket':
                if datadic['state'] == 'close':
                    # self.isBitmexDataOK = False
                    isOkexRun = False
                elif datadic['state'] == 'open':
                    self.isOkexDataOK = True

        elif type(datadic) == list and 'channel' in datadic[0] and datadic[0]['channel'] == 'ok_sub_futureusd_btc_depth_quarter_5':
            # print(datadic)
            data = datadic[0]['data']
            self.sells5 = data['asks'][::-1]
            self.buys5 = data['bids']
            self.okexDatas = [self.buys5[0],self.sells5[0],int(time.time())]             #买一价，卖一价，接收数据时间
            self.updateDataSub()
            # print(self.buys5[0],self.sells5[0])
        
        elif type(datadic) == list and 'channel' in datadic[0] and datadic[0]['channel'] == 'ok_sub_futureusd_trades':
            #合约定单数据更新
# amount(double): 委托数量
# contract_name(string): 合约名称
# created_date(long): 委托时间
# create_date_str(string):委托时间字符串
# deal_amount(double): 成交数量
# fee(double): 手续费
# order_id(long): 订单ID
# price(double): 订单价格
# price_avg(double): 平均价格
# status(int): 订单状态(0等待成交 1部分成交 2全部成交 -1撤单 4撤单处理中)
# symbol(string): btc_usd   ltc_usd   eth_usd   etc_usd   bch_usd
# type(int): 订单类型 1：开多 2：开空 3：平多 4：平空
# unit_amount(double):合约面值
# lever_rate(double):杠杆倍数  value:10/20  默认10
# system_type(int):订单类型 0:普通 1:交割 2:强平 4:全平 5:系统反单
        # [{u'binary': 0, u'data': 
        #{u'orderid': 1270246017934336, 
        #u'contract_name': u'BTC0928', 
        #u'fee': 0.0, 
        #u'user_id': 2051526, 
        #u'contract_id': 201809280000012, 
        #u'price': 1000.0, 
        #u'create_date_str': u'2018-08-13 08:00:16', 
        #u'amount': 1.0, 
        #u'status': 0, 
        #u'system_type': 0, 
        #u'unit_amount': 100.0, 
        #u'price_avg': 0.0, 
        #u'contract_type': u'quarter', 
        #u'create_date': 1534118416047, 
        #u'lever_rate': 20.0, 
        #u'type': 1, 
        #u'deal_amount': 0.0}, 
        #u'channel': u'ok_sub_futureusd_trades'}]

#okex彻单返回
# [{u'binary': 0, u'data': {u'orderid': 1304160027118592, u'contract_name': u'BTC0928', u'fee': 0.0, u'user_id': 2051526, u'contract_id': 201809280000012, u'price': 1000.0, u'create_date_str': u'2018-08-19 07:45:02', u'amount': 1.0, u'status': -1, u'system_type': 0, u'unit_amount': 100.0, u'price_avg': 0.0, u'contract_type': u'quarter', u'create_date': 1534635902000, u'lever_rate': 20.0, u'type': 1, u'deal_amount': 0.0}, u'channel': u'ok_sub_futureusd_trades'}]
            print(datadic)
            if datadic[0]['data']['status'] == -1:#撤单
                odata = datadic[0]['data']
                if str(odata['orderid']) in self.okexOIDDic:
                    tmpcid = self.okexOIDDic[str(odata['orderid'])]
                    # msg = {'type':'ol','amount':datadic['data']['amount'],'price':self.okexDatas[1][0]+5,'islimit':1,'cid':ocid}
                    # self.oCIDData = {'msg':msg,'state':0,'cid':datadic['data']['cid']}
                    if tmpcid != 'sssss':
                        trademsg = self.oCIDData[tmpcid]['msg']
                        #重新按市价设置将临价格
                        if trademsg['type'] == 'ol' or trademsg['type'] == 'cs':
                            trademsg['price'] = self.okexDatas[1][0]+5
                        elif trademsg['type'] == 'os' or trademsg['type'] == 'cl':
                            trademsg['price'] = self.okexDatas[0][0]-5

                        if self.tradeState > 200 and self.tradeState%10 == 3:
                            self.tradeState = self.tradeState - 2 #213,223,233,243加2后个位数都会变成5,okex撤单成功，重新下单
                        else:
                            print('self.tradeState erro:%d'%(self.tradeState))
                            if trademsg['type'] == 'ol':
                                self.tradeState = 211
                            elif trademsg['type'] == 'os':
                                self.tradeState = 221
                            elif trademsg['type'] == 'cl':
                                self.tradeState = 231
                            elif trademsg['type'] == 'cs':
                                self.tradeState = 241
                        self.oCIDData[tmpcid] = {'msg':trademsg,'state':0,'cid':tmpcid}
                        isSendOK = self.sendMsgToOkexTrade(trademsg['type'], trademsg)
                        while not isSendOK:
                            print('send okex trade ol erro...')
                            time.sleep(1)
                            isSendOK = self.sendMsgToOkexTrade(trademsg['type'], trademsg)
                        smsg = 'okex撤单成功，重新下单并重新下单，价格:%.2f'%(trademsg['price'])
                        sayMsg(smsg.encode())
                    else:
                        print('测试定单'.encode())
                else:
                    print('手动撤单。。。'.encode())
            elif datadic[0]['data']['status'] == 0:#已下单等成交
                tradeType = datadic[0]['data']['type']
                if tradeType == '1':
                    # outtype = 'ol'
                    self.tradeState = 212
                elif tradeType == '2':
                    # outtype = 'os'
                    self.tradeState = 222
                elif tradeType == '3':
                    # outtype = 'cl'
                    self.tradeState = 232
                elif tradeType == '4':
                    # outtype = 'cs'
                    self.tradeState = 242
            elif datadic[0]['data']['status'] == 2:#okex定单完全成交
                self.tradeState = 0    #okex完全成交，可以开新的bitmex定单
                tmpcid = self.okexOIDDic.pop(str(datadic[0]['data']['orderid']))

                bitmexMsg = self.bCIDData.pop(tmpcid)
                okexMsg = self.oCIDData.pop(tmpcid)
                # orderType + '-' + str(self.boCount) + '-' + str(int(time.time()))
                harddatas = tmpcid.split('-')
                #完成一个交易周期，记录交易数据到文件
                rbprice = bitmexMsg['msg']['price']
                roprice = datadic[0]['data']['price_avg']
                ramount = okexMsg['msg']['amount']
                rsub = '%.2f'%(roprice - rbprice)
                savedic = {'time':harddatas[2],'type':harddatas[0],'index':harddatas[1],'rsub':float(rsub),'rbprice':rbprice,'roprice':roprice,'amount':ramount,'bitmex':bitmexMsg,'okex':okexMsg}
                jstr = json.dumps(savedic) + '\n'
                f = open('tradelog.txt','a')
                f.write(jstr)
                f.close()
                smsg = 'okex完全成交，真实差价为%s'%(rsub)
                sayMsg(smsg.encode())


        elif type(datadic) == list and 'channel' in datadic[0] and datadic[0]['channel'] == 'ok_sub_futureusd_userinfo':
            #用户帐户数据更新
# 全仓信息
# balance(double): 账户余额
# symbol(string)：币种
# keep_deposit(double)：保证金
# profit_real(double)：已实现盈亏
# unit_amount(int)：合约价值
# 逐仓信息
# balance(double):账户余额
# available(double):合约可用
# balance(double):合约余额
# bond(double):固定保证金
# contract_id(long):合约ID
# contract_type(string):合约类别
# freeze(double):冻结
# profit(double):已实现盈亏
# unprofit(double):未实现盈亏
# rights(double):账户权益
        #[{u'binary': 0,
        # u'data': {
            #u'contracts': [
                #{u'available': 0.01223452, 
                #u'bond': 0.0, 
                #u'contract_id': 201809280000012, 
                #u'profit': 0.0, 
                #u'freeze': 0.005, 
                #u'long_order_amount': 0.0, 
                #u'short_order_amount': 0.0, 
                #u'balance': 0.0, 
                #u'pre_short_order_amount': 0.0, 
                #u'pre_long_order_amount': 1.0}], 
            #u'symbol': u'btc_usd',
            # u'balance': 0.01723452},
        # u'channel': u'ok_sub_futureusd_userinfo'}]
            print(datadic)
    
        elif type(datadic) == list and 'channel' in datadic[0] and datadic[0]['channel'] == 'ok_sub_futureusd_positions':
            #ok_sub_futureusd_positions,仓位数据更新
# 全仓说明
# position(string): 仓位 1多仓 2空仓
# contract_name(string): 合约名称
# costprice(string): 开仓价格
# bondfreez(string): 当前合约冻结保证金
# avgprice(string): 开仓均价
# contract_id(long): 合约id
# position_id(long): 仓位id
# hold_amount(string): 持仓量
# eveningup(string): 可平仓量
# margin(double): 固定保证金
# realized(double):已实现盈亏

# 逐仓说明
# contract_id(long): 合约id
# contract_name(string): 合约名称
# avgprice(string): 开仓均价
# balance(string): 合约账户余额
# bondfreez(string): 当前合约冻结保证金
# costprice(string): 开仓价格
# eveningup(string): 可平仓量
# forcedprice(string): 强平价格
# position(string): 仓位 1多仓 2空仓
# profitreal(string): 已实现盈亏
# fixmargin(double): 固定保证金
# hold_amount(string): 持仓量
# lever_rate(double): 杠杆倍数
# position_id(long): 仓位id
# symbol(string): btc_usd   ltc_usd   eth_usd   etc_usd   bch_usd  eos_usd  xrp_usd btg_usd 
# user_id(long):用户ID
    #[{u'binary': 0, u'data': 
        #{u'positions': 
            #[{u'contract_name': u'BTC0928',
            # u'balance': 0.0, u'contract_id': 201809280000012, 
            #u'fixmargin': 0, u'position_id': 1157028442213376, 
            #u'avgprice': 0, u'eveningup': 0, u'profitreal': 0.0,
            # u'hold_amount': 0, u'costprice': 0, 
            #u'position': 1, u'lever_rate': 10, 
            #u'bondfreez': 0.005, u'forcedprice': 0}, 
        #{u'contract_name': u'BTC0928', u'balance': 0.0, 
            #u'contract_id': 201809280000012, u'fixmargin': 0, 
            #u'position_id': 1157028442213376, u'avgprice': 0, 
            #u'eveningup': 0, u'profitreal': 0.0, u'hold_amount': 0, 
            #u'costprice': 0, u'position': 2, u'lever_rate': 10, 
            #u'bondfreez': 0.005, u'forcedprice': 0}, 
        #{u'contract_name': u'BTC0928', u'balance': 0.0, 
            #u'contract_id': 201809280000012, u'fixmargin': 0.0, 
            #u'position_id': 1157028442213376, u'avgprice': 7070.17, 
            #u'eveningup': 0.0, u'profitreal': 0.0, u'hold_amount': 0.0, 
            #u'costprice': 7070.17, u'position': 1, u'lever_rate': 20, 
            #u'bondfreez': 0.005, u'forcedprice': 0.0}, 
        #{u'contract_name': u'BTC0928', u'balance': 0.0, 
            #u'contract_id': 201809280000012, u'fixmargin': 0.0, 
            #u'position_id': 1157028442213376, u'avgprice': 7834.0, 
            #u'eveningup': 0.0, u'profitreal': 0.0, u'hold_amount': 0.0, 
            #u'costprice': 7834.0, u'position': 2, u'lever_rate': 20,
            # u'bondfreez': 0.005, u'forcedprice': 0.0}], u'symbol': u'btc_usd',
            # u'user_id': 2051526}, 
    #u'channel': u'ok_sub_futureusd_positions'}]
            print(datadic)
        # onOkexData
        if isOkexRun:
            self.isOkexDataOK = True
        else:
            self.isOkexDataOK = False

        self.lastimedic['od'] = int(time.time())


    #交易下单返回状态
    def onOkexTradeBack(self,datadic):
        isSayOpen = True
        if 'type' in datadic:
            if datadic['type'] == 'pong':
                self.socketstate['ot'] = True
                # print('pong from okex trade http server...')
            elif datadic['type'] == 'ol':
                if datadic['data']['result'] == False:
                    #'{"type":"trade","state":"erro","orderType":"%s","amount":%s,"price":%s}'%(outtype,amount,price)
                    
                    #okex开多失败，要求重新开多,刚在1秒后重新发送开多
                    msg = {'type':'ol','amount':datadic['data']['amount'],'price':self.okexDatas[1][0]+5,'islimit':1,'cid':datadic['cid']}
                    self.oCIDData[datadic['cid']] = {'msg':msg,'state':0,'cid':datadic['cid']}
                    if isSayOpen:
                        sayMsg('okex开多失败,1秒后重开多'.encode())
                    print(datadic)
                    time.sleep(1)
                    self.tradeState = 211 #211.okex开多正在下单
                    isSendOK = self.sendMsgToOkexTrade('ol', msg)
                    while not isSendOK:
                        print('okex trade server erro resend trade ol')
                        time.sleep(1)
                        isSendOK = self.sendMsgToOkexTrade('ol', msg)
                    # self.tradeState = 212 #212.okex开多已发送，等成交
                else:
                    #{"type":"ol","cid":"sssss","data":{"result":true,"order_id":1304160027118592}}
                    okexoid = str(datadic['data']['order_id'])
                    self.okexOIDDic[okexoid] = datadic['cid']


            elif datadic['type'] == 'cl':
                if datadic['data']['result'] == False:
                    #'{"type":"trade","state":"erro","orderType":"%s","amount":%s,"price":%s}'%(outtype,amount,price)
                    msg = {'type':'cl','amount':datadic['data']['amount'],'price':self.okexDatas[0][0]-5,'islimit':1,'cid':datadic['cid']}
                    self.oCIDData[datadic['cid']] = {'msg':msg,'state':0,'cid':datadic['cid']}
                    if isSayOpen:
                        sayMsg('okex平多失败,1秒后重平多'.encode())
                    print(datadic)
                    time.sleep(1) #延时1秒后重新下单
                    self.tradeState = 231 #231.okex平多正在下单
                    isSendOK = self.sendMsgToOkexTrade('cl', msg)
                    while not isSendOK:
                        print('okex trade server erro resend trade cl')
                        time.sleep(1)
                        isSendOK = self.sendMsgToOkexTrade('cl', msg)
                    # self.tradeState = 232 #232okex平多已发送，等成交 
                else:
                    okexoid = str(datadic['data']['order_id'])
                    self.okexOIDDic[okexoid] = datadic['cid']
            elif datadic['type'] == 'os':
                if datadic['data']['result'] == False:
                    #'{"type":"trade","state":"erro","orderType":"%s","amount":%s,"price":%s}'%(outtype,amount,price)
                    msg = {'type':'os','amount':datadic['data']['amount'],'price':self.okexDatas[0][0]-5,'islimit':1,'cid':datadic['cid']}
                    self.oCIDData[datadic['cid']] = {'msg':msg,'state':0,'cid':datadic['cid']}
                    if isSayOpen:
                        sayMsg('okex开空失败,1秒后重开空'.encode())
                    print(datadic)
                    time.sleep(1)
                    self.tradeState = 221 #221.okex开空正在下单
                    isSendOK = self.sendMsgToOkexTrade('os', msg)
                    while not isSendOK:
                        print('okex trade server erro resend trade os')
                        time.sleep(1)
                        isSendOK = self.sendMsgToOkexTrade('os', msg)
                    # self.tradeState = 222 #222.okex开空已发送，等成交
                else:
                    okexoid = str(datadic['data']['order_id'])
                    self.okexOIDDic[okexoid] = datadic['cid']
            elif datadic['type'] == 'cs':
                if datadic['data']['result'] == False:
                    #'{"type":"trade","state":"erro","orderType":"%s","amount":%s,"price":%s}'%(outtype,amount,price)
                    msg = {'type':'cs','amount':datadic['data']['amount'],'price':self.okexDatas[1][0]+5,'islimit':1,'cid':datadic['cid']}
                    self.oCIDData[datadic['cid']] = {'msg':msg,'state':0,'cid':datadic['cid']}
                    if isSayOpen:
                        sayMsg('okex平空失败,1秒后重平空'.encode())
                    print(datadic)
                    time.sleep(1)
                    self.tradeState = 241 #241.okex平空正在下单
                    isSendOK = self.sendMsgToOkexTrade('cs', msg)
                    while not isSendOK:
                        print('okex trade server erro resend trade cs')
                        time.sleep(1)
                        isSendOK = self.sendMsgToOkexTrade('cs', msg)
                    # self.tradeState = 242 #242.okex平空已发送，等成交
                else:
                    okexoid = str(datadic['data']['order_id'])
                    self.okexOIDDic[okexoid] = datadic['cid']
            elif datadic['type'] == 'pos': #返回合约持仓数量
                if datadic['data']['result'] == False:
                    #'{"type":"trade","state":"erro","orderType":"%s","amount":%s,"price":%s}'%(outtype,amount,price)
                    pass
            elif datadic['type'] == 'cancel':
                if datadic['data']['result'] == False:
                    #res = '{"result":false,"oid":"%s"}'%(orderId)
                    time.sleep(1)
                    isSendOK = self.cancelOneTrade('okex',datadic['oid'])
                    while not isSendOK:
                        print('okex trade server erro resend cancel okex trade')
                        time.sleep(1)
                        isSendOK = self.cancelOneTrade('okex',datadic['oid'])
                # else:
                    #okex取消定单完成,将重新下单
                    # self.tradeState = self.tradeState + 2 #213,223,233,243加2后个位数都会变成5
                    # time.sleep(1)       #等1秒后再重新下单


            elif datadic['type'] == 'account':
                if datadic['data']['result'] == False:
                    pass
            elif datadic['type'] == 'cancelall':
                if datadic['data']['result'] == False:
                    pass
            elif datadic['type'] == 'getID':
                if datadic['data']['result'] == False:
                    pass
            elif datadic['type'] == 'getall':
                if datadic['data']['result'] == False:
                    pass

        else:
            print(datadic)
        self.lastimedic['ot'] = int(time.time())
    # 取消某个定单
    # {type:cancel,id:123456}
    def cancelOneTrade(self,market,orderID):
        msg = {'type':'cancel','id':orderID}
        lastBiemexState = self.tradeState
        if market == 'okex':
            return self.sendMsgToOkexTrade('cancel', msg)
        elif market == 'bitmex':
            return self.sendMsgToBitmexTrade('cancel', msg)
        return False
    #bitmex数据
    def onBitmexData(self,datadic):
        isBitmexRun = True
        if 'type' in datadic:
            if datadic['type'] == 'pong':
                self.socketstate['bd'] = True
                # print('pong from bitmex ws data server...')
            elif datadic['type'] == 'socket':
                if datadic['state'] == 'close':
                    isBitmexRun = False
                    sayMsg('bitmex数据服务器关闭'.encode())
                elif datadic['state'] == 'open':
                    self.isBitmexDataOK = True
                    sayMsg('bitmex数据服务器关闭'.encode())
        elif 'table' in datadic and datadic['table'] == 'quote':
            datas = datadic['data']
            timeint,timestr = self.timeconvent(datas[-1]['timestamp'])
            self.selltop = [datas[-1]['askPrice'],datas[-1]['askSize'],timeint,timestr]
            self.buytop = [datas[-1]['bidPrice'],datas[-1]['bidSize'],timeint,timestr]
            self.bitmexDatas = [self.buytop,self.selltop,self.buytop[2]]           #买一价，卖一价, 接收数据时间
            self.updateDataSub()
            # print(self.buytop,self.selltop)
        elif 'table' in datadic and datadic['table'] == 'execution': #// 个别成交，可能是多个成交
            print('---execution--bitmex--')
            print(datadic)
        elif 'table' in datadic and datadic['table'] == 'order' and datadic['action'] != 'partial': #// 你委托的更新
            print('---order--bitmex--')
            # {u'action': u'insert', u'table': u'order', u'data': [{u'ordStatus': u'New', u'exDestination': u'XBME', u'text': u'Submitted via API.', u'timeInForce': u'GoodTillCancel', u'currency': u'USD', u'pegPriceType': u'', u'simpleLeavesQty': 0.0158, u'ordRejReason': u'', u'transactTime': u'2018-08-12T23:02:44.540Z', u'clOrdID': u'os-2-1534114964.188801', u'settlCurrency': u'XBt', u'cumQty': 0, u'displayQty': None, u'avgPx': None, u'price': 6340, u'simpleOrderQty': None, u'contingencyType': u'', u'triggered': u'', u'timestamp': u'2018-08-12T23:02:44.540Z', u'symbol': u'XBTUSD', u'pegOffsetValue': None, u'execInst': u'ParticipateDoNotInitiate', u'simpleCumQty': 0, u'orderID': u'13c79094-518a-c95b-fd95-3f090d339e6e', u'multiLegReportingType': u'SingleSecurity', u'account': 278343, u'stopPx': None, u'leavesQty': 100, u'orderQty': 100, u'workingIndicator': False, u'ordType': u'Limit', u'clOrdLinkID': u'', u'side': u'Sell'}]}
            #下单后websocket返回的状态改变数据
            # {u'action': u'update', u'table': u'order', u'data': [{u'orderID': u'71931c93-340d-9455-bf80-b0ac50797604', u'account': 278343, u'workingIndicator': True, u'timestamp': u'2018-08-12T21:13:37.105Z', u'symbol': u'XBTUSD', u'clOrdID': u''}]}
            #取消定单时的websocket返回的状态改变数据
            #{u'action': u'update', u'table': u'order', u'data': [{u'orderID': u'71931c93-340d-9455-bf80-b0ac50797604', u'account': 278343, u'ordStatus': u'Canceled', u'workingIndicator': False, u'text': u'Canceled: Canceled via API.\nSubmitted via API.', u'symbol': u'XBTUSD', u'leavesQty': 0, u'simpleLeavesQty': 0, u'timestamp': u'2018-08-12T21:15:44.581Z', u'clOrdID': u''}]}
            print(datadic)
            if 'ordStatus' in datadic['data'][0] and datadic['data'][0]['ordStatus'] == 'Canceled':#定单已取消
                self.onBitmexOrderCancelOK(datadic['data'][0])
            elif 'ordStatus' not in datadic['data'][0] and ('workingIndicator' in datadic['data'][0]) and datadic['data'][0]['workingIndicator']:
                self.onBitmexOrderOnline(datadic['data'][0]) #定单成功委托
            elif datadic['action'] == 'insert':#新增定单
                self.onBitmexOrderStart(datadic['data'][0])
            elif datadic['action'] == 'update' and datadic['data'][0]['ordStatus'] == 'Filled':#定单完全成交
            #{u'action': u'update', 
            #u'table': u'order', u'data': 
                #[{u'orderID': u'b4140470-66c8-dc3b-8f89-6c8cba4d107a', 
                #u'account': 278343, u'ordStatus': u'Filled', u'cumQty': 100, 
                #u'workingIndicator': False, u'timestamp': u'2018-08-13T00:44:11.725Z', 
                #u'symbol': u'XBTUSD', u'leavesQty': 0, u'simpleLeavesQty': 0, 
                #u'simpleCumQty': 0.01581, u'clOrdID': u'', 
                #u'avgPx': 6338}]}
                self.onBitmexTradeOK(datadic['data'][0])
        elif 'table' in datadic and datadic['table'] == 'margin': #你账户的余额和保证金要求的更新
            print('---margin--bitmex--')
            print(datadic)
        elif 'table' in datadic and datadic['table'] == 'position': #// 你仓位的更新
            print('---position--bitmex--')
            print(datadic)
        else:
            print('---other--bitmex--')
            print(datadic)
        if isBitmexRun:
            self.isBitmexDataOK = True
        else:
            self.isBitmexDataOK = False
        self.lastimedic['bd'] = int(time.time())

    #bitmex新增加定单委托
    def onBitmexOrderStart(self,data):
        if data['ordStatus'] == 'New':
            if data['clOrdID'] != '':
                
                # msg = {'type':'cl','amount':self.baseAmount*100,'price':self.bitmexDatas[0][0],'islimit':1,'cid':cid}
                # self.bCIDData[cid] = {'msg':msg,'state':0,'type':'cbo','sub':[]}
                msg = '新增定单,cid:%s'%(data['clOrdID'])
                print(msg.encode())
            else:
                print('网页上新增委托，没有cid'.encode())
            if data['workingIndicator']:
                self.onBitmexOrderOnline(data) #定单已成功委托
    #当下单已成功委托
    def onBitmexOrderOnline(self,data):
        if data['clOrdID'] in self.bCIDData:
            self.bCIDData[data['clOrdID']]['state'] = 1
            if data['clOrdID'] in self.bCIDData and self.bCIDData[data['clOrdID']]['msg']['type'] == 'ol':
                if self.tradeState < 200:
                    self.tradeState = 112
            elif data['clOrdID'] in self.bCIDData and self.bCIDData[data['clOrdID']]['msg']['type'] == 'os':
                if self.tradeState < 200:
                    self.tradeState = 122
            elif data['clOrdID'] in self.bCIDData and self.bCIDData[data['clOrdID']]['msg']['type'] == 'cl':
                if self.tradeState < 200:
                    self.tradeState = 132
            elif data['clOrdID'] in self.bCIDData and self.bCIDData[data['clOrdID']]['msg']['type'] == 'cs':
                if self.tradeState < 200:
                    self.tradeState = 142
        else:
            print("非交易对下单，已成功委托的定单ID为bitmex下单服务器自动生成,".encode())
            print(data)
    #当bitmex下单完全成交
    def onBitmexTradeOK(self,data):
        print(data)
        print(self.bCIDData)
        print(self.okexTradeMsgs)
        if data['clOrdID'] in self.bCIDData:
            self.bCIDData[data['clOrdID']]['state'] = 2
            ptype = self.okexTradeMsgs.pop(0)
            if ptype['cid'] == data['clOrdID']:
                print('cid is eq:%s'%(data['clOrdID']))
                ocid = ptype['cid']
                isSendOK = False
                self.tradecount = 0
                print('bitmex order Filled')
                # smsg = 'bitmex完全成交'.encode()
                # sayMsg(smsg)
                msg = {}
                if ptype['type'] == 'ol':
                    msg = {'type':'ol','amount':ptype['amount'],'price':self.okexDatas[1][0]+5,'islimit':1,'cid':ocid}
                    self.oCIDData[ocid] = {'msg':msg,'state':0,'cid':ocid}
                    print('okex open order')
                    self.tradeState = 211 #211.okex开多正在下单
                    isSendOK = self.sendMsgToOkexTrade('ol', msg)
                    while not isSendOK:
                        print('send okex trade ol erro...')
                        time.sleep(1)
                        isSendOK = self.sendMsgToOkexTrade('ol', msg)
                    self.tradeState = 212 #212.okex开多已发送，等成交
                elif ptype['type'] == 'os':
                    msg = {'type':'os','amount':ptype['amount'],'price':self.okexDatas[0][0]-5,'islimit':1,'cid':ocid}
                    self.oCIDData[ocid] = {'msg':msg,'state':0,'cid':ocid}
                    self.tradeState = 221#221.okex开空正在下单
                    isSendOK = self.sendMsgToOkexTrade('os', msg)
                    while not isSendOK:
                        print('send okex trade os erro...')
                        time.sleep(1)
                        isSendOK = self.sendMsgToOkexTrade('os', msg)
                    self.tradeState = 222 #212.okex开多已发送，等成交
                elif ptype['type'] == 'cl':
                    msg = {'type':'cl','amount':ptype['amount'],'price':self.okexDatas[0][0]-5,'islimit':1,'cid':ocid}
                    self.oCIDData[ocid] = {'msg':msg,'state':0,'cid':ocid}
                    self.tradeState = 231 #231.okex平多正在下单
                    isSendOK = self.sendMsgToOkexTrade('cl', msg)
                    while not isSendOK:
                        print('send okex trade cl erro...')
                        time.sleep(1)
                        isSendOK = self.sendMsgToOkexTrade('cl', msg)
                    self.tradeState = 232 #232.okex平多已发送，等成交 
                elif ptype['type'] == 'cs':
                    msg = {'type':'cs','amount':ptype['amount'],'price':self.okexDatas[1][0]+5,'islimit':1,'cid':ocid}
                    self.oCIDData[ocid] = {'msg':msg,'state':0,'cid':ocid}
                    self.tradeState = 241 #241.okex平空正在下单
                    isSendOK = self.sendMsgToOkexTrade('cs', msg)
                    while not isSendOK:
                        print('send okex trade cs erro...')
                        time.sleep(1)
                        isSendOK = self.sendMsgToOkexTrade('cs', msg)
                    self.tradeState = 242 #242.okex平空已发送，等成交
                if isSendOK:
                    print('okex open order sended')
                    # smsg = 'okex下单'
                    # sayMsg(smsg)
                    self.lastOkexTradeTime = int(time.time())
                    if self.baseOB > 0 and self.isCloseBaseOB:
                        self.isCloseBaseOB = False
                        if self.bCIDData[data['clOrdID']]['type'] == 'cob':
                            self.baseOB -= 1
                        elif self.bCIDData[data['clOrdID']]['type'] == 'coba':
                            self.baseOB = 0
                    elif self.baseBO > 0 and self.isCloseBaseBO:
                        self.isCloseBaseBO = False
                        if self.bCIDData[data['clOrdID']]['type'] == 'cbo':
                            self.baseBO -= 1
                        elif self.bCIDData[data['clOrdID']]['type'] == 'cboa':
                            self.baseBO = 0
                else:
                    print(msg)
                    print('okex open order erro')
                    # smsg = 'okex下单出错'.encode()
                    # sayMsg(smsg)
        else:
            # print("非交易对下单，完全成交的定单ID为bitmex下单服务器自动生成,".encode())
            print("ordercid is trade server create cid")
            print(data)

    
    #当bitmex定单取消成功
    def onBitmexOrderCancelOK(self,data):
        if data['clOrdID'] in self.bCIDData:
            self.nowTradeCID = ''
            tmpobj = self.bCIDData.pop(data['clOrdID'])
            msg = tmpobj['msg']
            deln  = -1
            for n in range(len(self.okexTradeMsgs)):
                d = self.okexTradeMsgs[n]
                if d['cid'] == msg['cid']:
                    deln = n
                    break
            if deln >= 0:
                self.okexTradeMsgs.pop(deln)
            if tmpobj['type'] == 'oob':
                self.obsubs.pop()
            elif tmpobj['type'] == 'cob' and tmpobj['sub']:
                self.obsubs.append(tmpobj['sub'][0])
            elif tmpobj['type'] == 'obo':
                self.bosubs.pop()
            elif tmpobj['type'] == 'cbo' and tmpobj['sub']:
                self.bosubs.append(tmpobj['sub'][0])
            elif tmpobj['type'] == 'coba' and tmpobj['sub']:
                self.obsubs = list(tmpobj['sub'])
            elif tmpobj['type'] == 'cboa' and tmpobj['sub']:
                self.bosubs = list(tmpobj['sub'])
            self.tradeState = 0 #0.没有下单，可下新单
            smsg = 'bitmex撤单成功'
            sayMsg(smsg)
            self.lastBitmexTradeTime = int(time.time()) + 27     #定单取消时，等27+3=30秒再开始下一个交易
        else:
            # print("非交易对下单，已成功取消的定单ID为bitmex下单服务器自动生成,".encode())
            print(self.bCIDData)
            print(data)

    #bitmex下单服务器反回下单情况
    def onBitmexTradeBack(self,datadic):
        if 'type' in datadic and datadic['type'] == 'pong':
            self.socketstate['bt'] = True
            # print('pong from bitmex trade http server...')
        elif 'servererro' in datadic:
            print('bitmex下单交易服务器返回错误'.encode())
            print(datadic['servererro'])
            self.onBitmexTradeServerErro(datadic['data'])
        else:
            print(datadic)
            
        self.lastimedic['bt'] = int(time.time())

    #bitmex下单出错，对错误进行处理
    def onBitmexTradeServerErro(self,tdata):
        # {"data": {"amount": 100, "type": "os", "price": 6462.5, "islimit": 1, "cid": "oob-1-1534784579"}, "sign": "2B304F1249175C2A960F8D3034A2B9EA290BAD812902810C15409406EEC9EB82", "type": "os", "time": 1534784579}
        senddata = tdata['data']
        self.nowTradeCID = ''
        if senddata['cid'][:5] == 'sssss':
            print('测试手动下单，服务器错误'.encode())
            print(tdata)
            self.clearCache()
            return
        tmpobj = self.bCIDData.pop(senddata['cid'])
        msg = tmpobj['msg']
        deln  = -1
        for n in range(len(self.okexTradeMsgs)):
            d = self.okexTradeMsgs[n]
            if d['cid'] == msg['cid']:
                deln = n
                break
        if deln >= 0:
            self.okexTradeMsgs.pop(deln)
        if tmpobj['type'] == 'oob':
            self.obsubs.pop()
        elif tmpobj['type'] == 'cob' and tmpobj['sub']:
            self.obsubs.append(tmpobj['sub'][0])
        elif tmpobj['type'] == 'obo':
            self.bosubs.pop()
        elif tmpobj['type'] == 'cbo' and tmpobj['sub']:
            self.bosubs.append(tmpobj['sub'][0])
        elif tmpobj['type'] == 'coba' and tmpobj['sub']:
            self.obsubs = list(tmpobj['sub'])
        elif tmpobj['type'] == 'cboa' and tmpobj['sub']:
            self.bosubs = list(tmpobj['sub'])
        self.tradeState = 0 #0.没有下单，可下新单
        self.lastBitmexTradeTime = int(time.time()) + 27   #等5秒后才会重新下单，因为默认是等27+3=30秒，这里加12秒记等15秒后再会重新开始下单
        smsg = 'bitmex下单错误'.encode()
        sayMsg(smsg)




    
    # self.initBitmexDataSocket()
    def sendMsgToBitmexData(self,ptype,msg,isSigned = False):
        try:
            if self.bitmexDataSocket:
                if isSigned:
                    outobj = {'type':ptype,'time':int(time.time()),'sign':'issigned','data':msg}
                    outstr = json.dumps(outobj)
                    self.bitmexDataSocket.send(outstr.encode())
                else:
                    ptime = int(time.time())
                    sign = signTool.signMsg(msg,ptime,self.bitmexSeckey)
                    outobj = {'type':ptype,'time':ptime,'sign':sign,'data':msg}
                    outstr = json.dumps(outobj)
                    self.bitmexDataSocket.send(outstr.encode())
                return True
            else:
                print("没有bitmexDataSocket客户端连接".encode())
                self.initBitmexDataSocket()
                return False
        except Exception as e:
            print('服务器端bitmexDataSocket网络错误1'.encode())
            self.initBitmexDataSocket()
            return False

    # self.initBitmexTradeSocket()
    def sendMsgToBitmexTrade(self,ptype,msg,isSigned = False):
        # try:
        if True:
            if self.bitmexTradeSocket:
                if isSigned:
                    outobj = {'type':ptype,'time':int(time.time()),'sign':'issigned','data':msg}
                    outstr = json.dumps(outobj)
                    self.bitmexTradeSocket.send(outstr.encode('utf-8'))
                else:
                    ptime = int(time.time())
                    sign = signTool.signMsg(msg,ptime,self.bitmexSeckey)
                    outobj = {'type':ptype,'time':ptime,'sign':sign,'data':msg}
                    outstr = json.dumps(outobj)
                    print(outstr)
                    self.bitmexTradeSocket.send(outstr.encode('utf-8'))
                return True
            else:
                print("no heave bitmexTradeSocket client connect")
                self.initBitmexTradeSocket()
                return False
        # except Exception as e:
        #     print('server bitmexTradeSocket net erro 1')
        #     return False
    
    # self.initOkexDataSocket()
    def sendMsgToOkexData(self,ptype,msg,isSigned = False):
        try:
            if self.okexDataSocket:
                if isSigned:
                    outobj = {'type':ptype,'time':int(time.time()),'sign':'issigned','data':msg}
                    outstr = json.dumps(outobj)
                    self.okexDataSocket.send(outstr.encode('utf-8'))
                else:
                    ptime = int(time.time())
                    sign = signTool.signMsg(msg,ptime,self.okexSeckey)
                    outobj = {'type':ptype,'time':ptime,'sign':sign,'data':msg}
                    outstr = json.dumps(outobj)
                    self.okexDataSocket.send(outstr.encode('utf-8'))
                return True
            else:
                print("没有okexDataSocket客户端连接".encode())
                self.initOkexDataSocket()
                return False
        except Exception as e:
            print('服务器端okexDataSocket网络错误1'.encode())
            self.initOkexDataSocket()
            return False

    # self.initOkexTradeSocket()
    def sendMsgToOkexTrade(self,ptype,msg,isSigned = False):
        try:
            if self.okexTradeSocket:
                if isSigned:
                    outobj = {'type':ptype,'time':int(time.time()),'sign':'issigned','data':msg}
                    outstr = json.dumps(outobj)
                    self.okexTradeSocket.send(outstr.encode())
                else:
                    ptime = int(time.time())
                    sign = signTool.signMsg(msg,ptime,self.okexSeckey)
                    outobj = {'type':ptype,'time':ptime,'sign':sign,'data':msg}
                    outstr = json.dumps(outobj)
                    self.okexTradeSocket.send(outstr.encode())
                return True
            else:
                print("没有okexDataSocket客户端连接".encode())
                self.initOkexTradeSocket()
                return False
        except Exception as e:
            print('服务器端okexTradeSocket网络错误1'.encode())
            self.initOkexTradeSocket()
            return False
    
    #当有客户端30秒没有接收到数据时就发送ping
    def pingAllServer(self,ptimeDelay = 30):
        ptime = int(time.time())
        for k in self.socketstate.keys():
            if ptime - self.lastimedic[k] > ptimeDelay:
                self.socketstate[k] = False
            else:
                self.socketstate[k] = True
        if not self.socketstate['bd']:
            self.sendMsgToBitmexData('ping','ping',isSigned = True)
        if not self.socketstate['bt']:
            self.sendMsgToBitmexTrade('ping','ping',isSigned = True)
        if not self.socketstate['od']:
            self.sendMsgToOkexData('ping','ping',isSigned = True)
        if not self.socketstate['ot']:
            self.sendMsgToOkexTrade('ping','ping',isSigned = True)
    def printSet(self):
        print('isTest:',self.isTest)
        print('amount:',self.amount)

    def cleanAllTrade(self):
        pass


def main():
     pass
if __name__ == '__main__':
    main()
   
