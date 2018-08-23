#!/usr/bin/python
# -*- coding: utf-8 -*-
#用于访问OKCOIN 期货REST API

import websocket
import socket
import sys
import hmac
import hashlib

try:
    import thread
except ImportError:
    import _thread as thread
import time
import json
from magetool import timetool
from future.builtins import bytes


class bitmexWSTool(object):
    """docstring for wsDataTool"""
    def __init__(self,psecret):
        super(bitmexWSTool, self).__init__()

        self.secret = psecret
        self.selltop = []
        self.buytop = []

        self.csocket = None


        self.lastPingTime = int(time.time())

        self.sendcount = 100   #每100次log提示一次没有客户端连接
        

        #每一个周期里包括，开多，涨价，平多，价跌，开空，跌价，平空，涨价，8个价位测试，
        #涨价和跌价主要为了测试，价络改变后的自动取消和自动再下单操作

        #下单状态，ok:返回已完全成交,cancel:取消定单，市场价格下降，市场价格上涨

        self.lastPrice = 0
        self.lastType = ''


        self.text = ''
        self.basePrice = 6000
        self.bssub = 1
        self.obSub = 2
        self.isRun = 0
        self.stepChange = 0

        self.readTestConfig()

    def readTestConfig(self):
#         {
#     "basePrice":6000,
#     "bssub":1,
#     "obSub":2,
#     "tradeState":1,
#     "isRun":0,
#     "stepChange":0,
#     "text":"oob_cob_obo_cbo"
# }
        f = open('../tradeconfig.json','r')
        strdat = f.read()
        f.close()
        datadic = json.loads(strdat)
        self.text = datadic['text']                 #当前测试类型
        self.basePrice = datadic['basePrice']       #测试基本价格，其他价格在此基础上作改变
        self.bssub = datadic['bssub']               #买卖价之间的差价
        self.obSub = datadic['obSub']               #okex和bitmex的差价，值为负表示okex小于bitmex
        self.isRun = datadic['isRun']               #是否启动差价系统，当为0是okex和bitmex的价格都为basePrice,即两者没有差价
        self.tradeState = datadic['tradeState']     #交易下单返回状态，当为0表示下单为取消，1时表示下单为完全成交,2表示bitmex为取消okex为完全成交，3表示bitmex为完全成交okex为取消,
        isChange = self.stepChange != datadic['stepChange']
        self.stepChange = datadic['stepChange']
        print(self.text)
        return isChange

    def getMarketData(self):
        buy = self.basePrice
        sell = self.basePrice + self.bssub
        tmpdata = {"table":"quote","action":"insert","data":[{"timestamp":"2018-08-15T14:57:10.278Z","symbol":"XBTUSD","bidSize":1591830,"bidPrice":buy,"askPrice":sell,"askSize":38682}]}
        return tmpdata
    #接收来自测试下单服务器的消息
    def reciveMsgFromTestTradeServer(self,msgdic):
        print(msgdic)
        # {u'price': 6374.5, u'type': u'os', u'amount': 100, u'cid': u'b-os-1-1534368391'}
        #{'type':下单类型,price:下单价格,amount:下单数量,cid:下单用户ID},下单类型分为:开多，开空，平多，平空，取消定单5种
        #所要测试的状态
        self.lastPrice = msgdic['price']
        self.lastType = msgdic['type']

        self.readTestConfig()

        if self.lastType == 'cancel':
            print('发送交易取消数据')
            self.sendTradeCanel(msgdic['cid'])
        else:
            if self.tradeState == 1 or self.tradeState == 3:#当前返回状态为完成成交消息
                print('发送完全成交数据')
                self.sendTradeOK(msgdic['cid'], msgdic['price'], msgdic['amount'])
            elif self.tradeState == 0 or self.tradeState == 2:#当前返回状态为 交易取消
                print('发送交易取消数据')
                self.sendTradeCanel(msgdic['cid'])
        #1.完成成交，
        #2.定单取消
        #3,市价下跌
        #4,市价上涨

    #发送已完全成交消息给管理服务器
    def sendTradeOK(self,cid,price,amount):
        backmsg = {'action': 'update','table': 'order', 'data':[{
        'orderID':'b4140470-66c8-dc3b-8f89-6c8cba4d107a','account': 278343, 'ordStatus': 'Filled', 'cumQty': amount, 
                'workingIndicator': False, 'timestamp': '2018-08-13T00:44:11.725Z', 
                'symbol': 'XBTUSD', 'leavesQty': 0, 'simpleLeavesQty': 0, 
                'simpleCumQty': 0.01581, 'clOrdID': cid, 
                'avgPx': price}]}

        
        msg = json.dumps(backmsg)
        print(msg)
        self.sendMsgToClient(msg)
        

    def sendTradeCanel(self,cid):
        backmsg = {'action': 'update',
        'table': 'order', 
        'data': [{'orderID':'71931c93-340d-9455-bf80-b0ac50797604', 
            'account': 278343, 
            'ordStatus': 'Canceled',
             'workingIndicator': False, 
             'text': 'Canceled: Canceled via API.\nSubmitted via API.', 
             'symbol': 'XBTUSD', 
             'leavesQty': 0, 
             'simpleLeavesQty': 0, 
             'timestamp': '2018-08-12T21:15:44.581Z',
              'clOrdID': cid}]}

        msg = json.dumps(backmsg)
        print(msg)
        self.sendMsgToClient(msg)
        

    def sendDeepDataToClient(self):
        # {"table":"quote","action":"insert","data":[{"timestamp":"2018-08-15T14:57:10.278Z","symbol":"XBTUSD","bidSize":1591830,"bidPrice":6374,"askPrice":6374.5,"askSize":38682}]}
        isChange = self.readTestConfig()
        if isChange:
            dicdat = self.getMarketData()
            if self.isRun == 0:
                dicdat['data'][0]['bidPrice'] = self.basePrice
                dicdat['data'][0]['askPrice'] = self.basePrice + self.bssub
            msg = json.dumps(dicdat)
            self.sendMsgToClient(msg)
            self.updateTopDeep(dicdat['data'])

    def updateTopDeep(self,datas):
        if len(datas) > 0:
            timeint,timestr = self.timeconvent(datas[-1]['timestamp'])
            self.selltop = [datas[-1]['askPrice'],datas[-1]['askSize'],timeint,timestr]
            self.buytop = [datas[-1]['bidPrice'],datas[-1]['bidSize'],timeint,timestr]
            print(self.buytop,self.selltop)
        else:
            print('数据错误')

    def setSocketClient(self,clientsocket):
        self.csocket = clientsocket

    def reciveMsgFromClient(self,msgdic):
        print(msgdic)
        self.sendMsgToClient(str(msgdic))

    def sendMsgToClient(self,msg):
        def run(*args):
            try:
                if self.csocket:
                    self.csocket.send(msg.encode())
                else:
                    self.sendcount -= 1
                    if self.sendcount < 0:
                        self.sendcount = 100
                        print("没有客户端连接")
            except Exception as e:
                self.csocket = None
                print('客户端网络错误1')
        thread.start_new_thread(run, ())

    def timeconvent(self,utcstrtime):
        timest = timetool.utcStrTimeToTime(utcstrtime)
        timeint = int(timest)
        ltimeStr = str(timetool.timestamp2datetime(timeint,True))   
        return timeint,ltimeStr 
    

    def onMessage(self,msg):                #收到新的推送数据
        datdic = json.loads(msg)
        if 'table' in datdic:
            # self.sendMsgToClient(msg.encode())
            if datdic['table'] == 'tradeBin1m': #得到1分钟k线相关数据
                pass
            elif datdic['table'] == 'quote': #得到最高级深度数据更新
                # self.updateTopDeep(datdic['data'])
                print(msg)
    # "execution:XBTUSD","order:XBTUSD","margin:XTBUSD","position:XTBUSD"]
            elif datdic['table'] == 'execution':
                print(msg)
            elif datdic['table'] == 'order':
                print(msg)
            elif datdic['table'] == 'margin':
                print(msg)
            elif datdic['table'] == 'position':
                print(msg)
            else:
                print(msg)
        else:
            # print(msg)
            pass


def main():
    bitwstool = bitmexWSTool(None,None)
    bitwstool.wsRunForever()

if __name__ == '__main__':
    main()

    
