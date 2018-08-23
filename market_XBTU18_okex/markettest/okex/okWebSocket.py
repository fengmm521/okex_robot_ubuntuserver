#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import time
import zlib
import hashlib
import websocket
import json
import thread
#okex
#websocket只用来定阅数据推送，下单使用rest的https接口发送

class okWSTool():
    def __init__(self,psecret):

        self.secret_key = psecret
        self.csocket = None

        self.sells5 = []
        self.buys5 = []


        self.objname = 'okex'

        self.sendcount = 100   #每100次log提示一次没有客户端连接

        self.lastPrice = 0.0
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
        buy = self.basePrice + self.obSub
        sell = self.basePrice + self.bssub + self.obSub
        tmpdata = [{"binary":0,"channel":"ok_sub_futureusd_btc_depth_quarter_5","data":{"asks":[[buy,150,2.3403,12.5319,803]],"bids":[[sell,150,0.2809,0.2809,18]],"timestamp":1534351230420}}]
        return tmpdata

    def sendDataTest(self):
        #[{"binary":0,"channel":"ok_sub_futureusd_btc_depth_quarter_5","data":{"asks":[[6409.26,150,2.3403,12.5319,803],[6408.64,20,0.312,10.1916,653],[6407.76,121,1.8883,9.8796,633],[6407.63,192,2.9964,7.9913,512],[6406.43,320,4.9949,4.9949,320]],"bids":[[6406.39,18,0.2809,0.2809,18],[6406.18,18,0.2809,0.5618,36],[6405.27,1181,18.4379,18.9997,1217],[6405.15,150,2.3418,21.3415,1367],[6405.11,128,1.9984,23.3399,1495]],"timestamp":1534351230420}}]
        #[{"binary":0,"channel":"ok_sub_futureusd_btc_depth_quarter_5","data":{"asks":[[6409.26,150,2.3403,12.5319,803]],"bids":[[6406.39,18,0.2809,0.2809,18]]],"timestamp":1534351230420}}]
        isChange = self.readTestConfig()
        if isChange:
            msgdic = self.getMarketData()
            if self.isRun == 0:#价格反向改变
                msgdic[0]['data']['asks'][0][0] = self.basePrice
                msgdic[0]['data']['bids'][0][0] = self.basePrice + self.bssub

            msg = json.dumps(msgdic)
            self.sendMsgToClient(msg)
            self.setDeeps(msgdic[0]['data'])
    #接收到测试下单服务器数据
    def reciveDataFromTestTrade(self,datadict):
        print(datadict)
        # {u'price': 6000.23, u'type': u'ol', u'amount': 1, u'cid': u'null'}
        #{'type':下单类型,price:下单价格,amount:下单数量,cid:下单用户ID},下单类型分为:开多，开空，平多，平空，取消定单5种
        #要返回的发送的交易状态信息
        self.readTestConfig()
        self.lastPrice = datadict['price']
        self.lastType = datadict['type']
        if self.lastType == 'cancel':
            print('发送交易取消数据')
            self.sendTradeCanel(datadict['cid'], datadict['amount'], datadict['price'], datadict['type'])
        else:
            if self.tradeState == 1 or self.tradeState == 2:#返回完全成交状态
                self.sendTradeOK(datadict['cid'], datadict['amount'], datadict['price'], datadict['type'])
            elif self.tradeState == 0 or self.tradeState == 3:#返回交易取消状态
                self.sendTradeCanel(datadict['cid'], datadict['amount'], datadict['price'], datadict['type'])

        #1.完全成交信息
        #2.定单取消信息
        #3.价格上涨信息
        #4.价格下跌信息
    def sendTradeCanel(self,tid,amount,price,ptype):
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
        sendtype = 0
        if ptype == 'ol':
            sendtype = 1
        elif ptype == 'os':
            sendtype = 2
        elif ptype == 'cl':
            sendtype = 3
        elif ptype == 'cs':
            sendtype = 4
        backmsg = [{u'binary': 0, u'data': 
        {'orderid': 1270246017934336, 
        'contract_name': 'BTC0928', 
        'fee': 0.0, 
        'user_id': 2051526, 
        'contract_id': 201809280000012, 
        'price': float(price), 
        'create_date_str': '2018-08-13 08:00:16', 
        'amount': float(amount), 
        'status': -1, 
        'system_type': 0, 
        'unit_amount': 100.0, 
        'price_avg': 0.0, 
        'contract_type': 'quarter', 
        'create_date': 1534118416047, 
        'lever_rate': 20.0, 
        'type': sendtype, 
        'deal_amount': 0.0}, 
        'channel': 'ok_sub_futureusd_trades'}]
        msg = json.dumps(backmsg)
        self.sendMsgToClient(msg)
    def sendTradeOK(self,tid,amount,price,ptype):
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
        sendtype = 0
        if ptype == 'ol':
            sendtype = 1
        elif ptype == 'os':
            sendtype = 2
        elif ptype == 'cl':
            sendtype = 3
        elif ptype == 'cs':
            sendtype = 4
        backmsg = [{u'binary': 0, u'data': 
        {'orderid': 1270246017934336, 
        'contract_name': 'BTC0928', 
        'fee': 0.0, 
        'user_id': 2051526, 
        'contract_id': 201809280000012, 
        'price': float(price), 
        'create_date_str': '2018-08-13 08:00:16', 
        'amount': float(amount), 
        'status': 2, 
        'system_type': 0, 
        'unit_amount': 100.0, 
        'price_avg': 0.0, 
        'contract_type': 'quarter', 
        'create_date': 1534118416047, 
        'lever_rate': 20.0, 
        'type': sendtype, 
        'deal_amount': 0.0}, 
        'channel': 'ok_sub_futureusd_trades'}]
        msg = json.dumps(backmsg)
        self.sendMsgToClient(msg)
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
                print('客户端网络错误')
                if self.csocket:
                    self.csocket.close()
                self.csocket = None
                return
        thread.start_new_thread(run, ())

    

    def setDeeps(self,datadic):
        self.sells5 = datadic['asks'][::-1]
        self.buys5 = datadic['bids']
        print(self.buys5[0],self.sells5[0])

    def setObjName(self,pname):
        self.objname = pname

    #事件回调函数
    def setSocketClient(self,clientsocket):
        self.csocket = clientsocket

    
        

    #收到来自数据处理的命令消息
    def reciveCmdFromClient(self,cmd):
        print(cmd)
        self.sendMsgToClient(str(cmd))


    def saveTestData(self,msg):
        f = open('testdata.txt','a')
        f.write(msg + '\n')
        f.close()

    def on_message(self,ws,data):
        # data = self.inflate(evt) #data decompress
        try:
            self.sendMsgToClient(data)
            datadic = json.loads(data)[0]
            chanle = datadic['channel']
            if chanle == 'ok_sub_futureusd_btc_depth_quarter_5':#深度全量数据
                # print(datadic)
                # self.setDeeps(datadic['data'])
                self.saveTestData(data)
            elif chanle == 'ok_sub_futureusd_trades':
                #交易数据更新
                self.onTrade(datadic)
            elif chanle == 'ok_sub_futureusd_positions': #合约持仓信息更新
                self.onPositionsChange(datadic)
            elif chanle == 'ok_sub_futureusd_userinfo':  #合约帐户信息更新
                self.onUserInfoChange(datadic)
            else:
                # print(data)
                pass
        except Exception as e:
            print('-'*20)
            print(data)


    
    #ping服务器查看连接是否断开
    #服务器未断开会返回{"event":"pong"}
    def pingServer(self):
        channelcmd = "{'event':'ping'}"
        self.wsocket.send(channelcmd);


def main():


    oktool = okWSTool()
    oktool.wsRunForever()
if __name__ == '__main__':
    main()