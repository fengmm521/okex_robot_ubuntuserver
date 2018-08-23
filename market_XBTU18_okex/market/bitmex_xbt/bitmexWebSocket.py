#!/usr/bin/python
# -*- coding: utf-8 -*-
#用于访问OKCOIN 期货REST API

import websocket
import socket
import sys
import os
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
    def __init__(self,apikey,secret):
        super(bitmexWSTool, self).__init__()
        self.klines = []
        self.deepdic = {}
        self.sellID = 0
        self.buyID = 0

        self.selltop = []
        self.buytop = []

        self.isDeepInit = False

        self.csocket = None

        self.apikey = apikey
        self.secret = secret

        self.mType = 'XBTU18'

        self.ws = None
        self.wsurl = "wss://www.bitmex.com/realtime"

        self.savedatas = []

        self.isWSOpen = False
        self.lastPingTime = int(time.time())

        self.removeSocketFlogFile()

        self.initWebSocket()

        self.sendcount = 100   #每100次log提示一次没有客户端连接

    def setBitmexMarketType(self,marketType):
        self.mType = marketType

    def removeSocketFlogFile(self):
        if os.path.exists('sokceterro.txt'):
            os.remove('sokceterro.txt')

    def setSocketClient(self,clientsocket):
        self.csocket = clientsocket

    def reciveMsgFromClient(self,msgdic):
        print(msgdic)
        self.sendMsgToClient(str(msgdic))

    def sendMsgToClient(self,msg):
        def run(*args):
            try:
                if self.csocket:
                    if type(msg) == str:
                        self.csocket.send(msg.encode())
                    elif type(msg) == bytes:
                        self.csocket.send(msg)
                    else:
                        print('msg type erro')
                        print(msg)
                else:
                    self.sendcount -= 1
                    if self.sendcount < 0:
                        self.sendcount = 100
                        print("没有客户端连接".encode())
            except Exception as e:
                self.csocket = None
                print('客户端网络错误1'.encode())
        thread.start_new_thread(run, ())
    def getNonceTime(self):
        return int(round(time.time() * 1000))

    def generate_signature(self,apikey,secret,nonce):
        message = 'GET/realtime' + str(nonce)
        signature = hmac.new(bytes(secret, 'utf8'), bytes(message, 'utf8'), digestmod=hashlib.sha256).hexdigest()
        return signature

    #用户登陆
    def loginWebSocket(self):
        ws = self.ws
        expires = self.getNonceTime()
        signature = self.generate_signature(self.apikey,self.secret,expires)
        def run(*args):
            msg = {"op": "authKeyExpires", "args": [self.apikey, expires, signature]}
            jstr = json.dumps(msg)
            ws.send(jstr)
            time.sleep(1) #等0.3秒登陆成功后获取个人帐户信息推送
            msg = {"op": "subscribe", "args": ["execution:%s"%(self.mType),"order:%s"%(self.mType),"margin:%s"%(self.mType),"position:%s"%(self.mType)]}
            jstr = json.dumps(msg)
            ws.send(jstr)
        thread.start_new_thread(run, ())

    def on_message(self,ws, message):
        # print('-----getMsg------')
        # print(message)
                # print(type(message))
        # msg = str(message)
        try:
            if message != 'pong':
                self.onMessage(message)
            else:
                print(message)
        except Exception as e:
            print(e)
            if message.decode() != 'pong':
                self.onMessage(message)
            else:
                print(message)
        
        ptime = int(time.time())
        if ptime - self.lastPingTime >= 300:
            self.lastPingTime = ptime
            self.ws.send('ping'.encode())

    def on_error(self,ws, error):
        print('-----eoor------')
        print(error)



    def on_close(self,ws):
        self.isWSOpen = False
        print("### closed ###")
        
        msg = '{"type":"socket","state":"close"}'
        self.sendMsgToClient(msg)
        time.sleep(0.3)
        f = open('sokceterro.txt','w')
        f.write('1')
        f.close()
        time.sleep(10)
        # while not self.isWSOpen:
        #     time.sleep(1)
        #     self.initWebSocket()
        #     time.sleep(5)

    def on_open(self,ws):
        self.isWSOpen = True
        def run(*args):
            #订阅主题是无需身份验证:
            # "announcement",// 网站公告
            # "chat",        // Trollbox 聊天室
            # "connected",   // 已连接用户/机器人的统计数据
            # "funding",     // 掉期产品的资金费率更新 每个资金时段发送（通常是8小时）
            # "instrument",  // 产品更新，包括交易量以及报价
            # "insurance",   // 每日保险基金的更新
            # "liquidation", // 进入委托列表的强平委托
            # "orderBookL2", // 完整的 level 2 委托列表
            # "orderBook10", //  前10层的委托列表，用传统的完整委托列表推送
            # "publicNotifications", // 全系统的告示（用于段时间的消息）
            # "quote",       // 最高层的委托列表
            # "quoteBin1m",  // 每分钟报价数据
            # "quoteBin5m",  // 每5分钟报价数据
            # "quoteBin1h",  // 每个小时报价数据
            # "quoteBin1d",  // 每天报价数据
            # "settlement",  // 结算信息
            # "trade",       // 实时交易
            # "tradeBin1m",  // 每分钟交易数据
            # "tradeBin5m",  // 每5分钟交易数据
            # "tradeBin1h",  // 每小时交易数据
            # "tradeBin1d",  // 每天交易数据
            #主题要求进行身份验证:
            # "affiliate",   // 邀请人状态，已邀请用户及分红比率
            # "execution",   // 个别成交，可能是多个成交
            # "order",       // 你委托的更新
            # "margin",      // 你账户的余额和保证金要求的更新
            # "position",    // 你仓位的更新
            # "privateNotifications", // 个人的通知，现时并未使用
            # "transact"     // 资金提存更新
            # "wallet"       // 比特币余额更新及总提款存款
            msg = {"op": "subscribe", "args": ["quote:%s"%(self.mType)]}
            # msg = {"op": "subscribe", "args": ["tradeBin1m:XBTUSD"]}
            # msg = "help"
            jstr = json.dumps(msg)
            ws.send(jstr)
        thread.start_new_thread(run, ())
        time.sleep(3)
        self.loginWebSocket()
        msg = '{"type":"socket","state":"open"}'
        self.sendMsgToClient(msg)
    def initWebSocket(self):
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(self.wsurl,
                                  on_message = self.on_message,
                                  on_error = self.on_error,
                                  on_close = self.on_close)
        self.ws.on_open = self.on_open

    def wsRunForever(self):
        # self.ws.run_forever(ping_interval=70, ping_timeout=10)
        self.ws.run_forever()

    
    def timeconvent(self,utcstrtime):
        timest = timetool.utcStrTimeToTime(utcstrtime)
        timeint = int(timest)
        ltimeStr = str(timetool.timestamp2datetime(timeint,True))   
        return timeint,ltimeStr 

    def saveDeepList(self):
        out = ''
        for d in self.savedatas:
            out += json.dumps(d) + '\n'
        f = open('bitmexdeep.txt','a')
        f.write(out)
        f.close()

    def updateTopDeep(self,datas):
        if len(datas) > 0:
            timeint,timestr = self.timeconvent(datas[-1]['timestamp'])
            self.selltop = [datas[-1]['askPrice'],datas[-1]['askSize'],timeint,timestr]
            self.buytop = [datas[-1]['bidPrice'],datas[-1]['bidSize'],timeint,timestr]
            print(self.buytop,self.selltop)
            self.savedatas.append([int(time.time()),self.buytop,self.selltop])
            if len(self.savedatas) >= 100:
                self.saveDeepList()
                self.savedatas = []
        else:
            print('数据错误'.encode())

    def onMessage(self,msg):                #收到新的推送数据
        datdic = json.loads(msg)
        if 'table' in datdic:
            self.sendMsgToClient(msg)
            if datdic['table'] == 'tradeBin1m': #得到1分钟k线相关数据
                self.onKlineMessage(datdic)
            elif datdic['table'] == 'orderBookL2':
                if datdic['action'] == 'partial':
                    # print(datdic['data'])
                    self.onDeepMessage(datdic)
                    self.isDeepInit = True
                elif self.isDeepInit:
                    self.onDeepChangeMessage(datdic)
            elif datdic['table'] == 'quote': #得到最高级深度数据更新
                self.updateTopDeep(datdic['data'])
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
            print(msg)
    def onDeepMessage(self,datdic):            #收到深度数据
        tmpdatas = datdic['data']
        isFind = False
        lastData = None
        for d in tmpdatas:
            self.deepdic[d['id']] = d
            if (not isFind) and lastData and lastData['side'] == 'Sell' and d['side'] == 'Buy':
                self.sellID = lastData['id']
                self.buyID = d['id']
                isFind = True
            elif (not isFind):
                lastData = d

    def updateBuySellID(self):
        ids = list(self.deepdic.keys())
        ids.sort()
        lastData = None
        isFind = False
        for k in ids:
            d = self.deepdic[k]
            if (not isFind) and lastData and lastData['side'] == 'Sell' and d['side'] == 'Buy':
                self.sellID = lastData['id']
                self.buyID = d['id']
                isFind = True
            elif (not isFind):
                lastData = d

    def getDeepTop(self):
        return self.selltop,self.buytop

    def getDeeps(self,deepcount = 5):
        ids = list(self.deepdic.keys())
        ids.sort(reverse = False)
        psell = ids.index(self.sellID)
        buys = ids[:psell]
        buys.sort(reverse = True)
        sells = ids[psell:]
        buyouts = []
        sellouts = []
        for b in buys[:deepcount]:
            d = self.deepdic[b]
            buyouts.append(d)
        for s in sells[:deepcount]:
            d = self.deepdic[s]
            sellouts.append(d)
        return sellouts,buyouts

    def onDeepChangeMessage(self,datdic):      #更新深度数据
        isBuySellChange = False
        if datdic['action'] == 'update':
            for d in datdic['data']:
                lastside = self.deepdic[d['id']]['side']
                self.deepdic[d['id']]['size'] = d['size']
                if lastside != d['side']:    #价格买卖状态改变
                    self.deepdic[d['id']]['side'] = d['side']
                    isBuySellChange = True

        elif datdic['action'] == 'delete':
            for d in datdic['data']:
                self.deepdic.pop(d['id'])
                if d['id'] == self.sellID or d['id'] == self.buyID:
                    isBuySellChange = True

        elif datdic['action'] == 'insert':
            for d in datdic['data']:
                self.deepdic[d['id']] = d
                if d['side'] == 'Sell' and d['id'] <= self.buyID:
                    isBuySellChange = True
                elif d['side'] == 'Buy' and d['id'] >= self.sellID:
                    isBuySellChange = True

        if isBuySellChange:
            self.updateBuySellID()

    def conventDataForSave(self,dat):
        # {'timestamp': '2018-03-14T15:17:00.000Z', 'symbol': 'XBTUSD', 'open': 8707.5, 'high': 8720, 'low': 8706, 'close': 8716.5, 'trades': 357, 'volume': 1488175, 'vwap': 8710.0427, 'lastSize': 500, 'turnover': 17086355694, 'homeNotional': 170.86355693999997, 'foreignNotional': 1488175},
        outs = []
        for d in dat:
            utctime = d['timestamp']
            timest = timetool.utcStrTimeToTime(utctime)
            timeint = int(timest)
            ltimeStr = timetool.timestamp2datetime(timeint,True)
            opentmp = d['open']
            hithtmp = d['high']
            lowtmp = d['low']
            closetmp = d['close']
            volumetmp = d['volume']
            symboltmp = d['symbol']
            outs.append([timeint,opentmp,hithtmp,lowtmp,closetmp,volumetmp,symboltmp,str(ltimeStr)])
        return outs
        #{"timestamp":"2018-06-18T04:33:00.000Z","symbol":"XBTUSD","open":6414.5,"high":6415,"low":6414.5,"close":6414.5,"trades":55,"volume":106981,"vwap":6415.1912,"lastSize":1000,"turnover":1667650020,"homeNotional":16.6765002,"foreignNotional":106981}

        #[1521199140, 8127, 8127, 8126.5, 8126.5, 225456, 'XBTUSD', '2018-03-16 19:19:00']

    def onKlineMessage(self,datdic):           #1分钟k线数据
        tmps = datdic['data']
        dats = self.conventDataForSave(tmps)

        self.klines += dats
        if len(self.klines) > 1200:              #保存最多1200条1分钟k线
            self.klines = self.klines[-1200:]
        #{"timestamp":"2018-06-18T04:33:00.000Z","symbol":"XBTUSD","open":6414.5,"high":6415,"low":6414.5,"close":6414.5,"trades":55,"volume":106981,"vwap":6415.1912,"lastSize":1000,"turnover":1667650020,"homeNotional":16.6765002,"foreignNotional":106981}

        #[1521199140, 8127, 8127, 8126.5, 8126.5, 225456, 'XBTUSD', '2018-03-16 19:19:00']

def main():
    bitwstool = bitmexWSTool()
    bitwstool.websocketRun_forever()

if __name__ == '__main__':
    main()

    
