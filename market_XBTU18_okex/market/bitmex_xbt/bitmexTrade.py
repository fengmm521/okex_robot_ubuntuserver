#!/usr/bin/python
# -*- coding: utf-8 -*-


import bitmex

import json
import datetime
import time
# kfpth = '../../../../btc/bitmex/key.txt'
# kfpth = '/Users/Allen/Documents/key/bitmexkey.txt'



class BitMexFuture:

    def __init__(self,apikey,secretkey,isTest = True):

        self.apikey = apikey
        self.secret = secretkey


        self.mType = 'XBTU18'
        self.client = bitmex.bitmex(test=False, api_key=apikey, api_secret=secretkey)
        # https://www.bitmex.com/realtime
        # https://www.bitmex.com/api/v1
        self.baseAmount = 100
        self.isTest = isTest

        self.csocket = None

        self.baseCID = 1

    def setBitmexMarketType(self,marketType):
        self.mType = marketType

    def setClientSocket(self,clientsocket):
        self.csocket = clientsocket

    def sendMsgToClient(self,msg):
        # try:
        if True:
            pmsg = msg
            if type(msg) == dict or type(msg) == list:
                pmsg = json.dumps(msg)
            elif type(msg) == tuple:
                pmsg = json.dumps(msg[0])
            if self.csocket:
                self.csocket.send(pmsg.encode())
            else:
                print("not client connect")
    def onTradeMsg(self,msgdict):
        
        bcmsg = ''
        
        if msgdict['type'] == 'ol':#open long
            # self.baseAmount = msgdict['amount']
            if self.isTest:
                bcmsg = '{"type":"bimex_test_ol"}'
            else:
                bcmsg = self.future_trade_xbtusd(msgdict['price'], msgdict['amount'],'ol',bool(msgdict['islimit']),clientID = msgdict['cid'])
            savestr = 'ol,price:%.1f,amount:%d,islimit:%d,bc:'%(msgdict['price'],msgdict['amount'],msgdict['islimit']) + str(bcmsg)
            self.testTradeSave(savestr)
            print(savestr)
        elif msgdict['type'] == 'cl':#close long
            if self.isTest:
                bcmsg = '{"type":"bimex_test_cl"}'
            else:
                bcmsg = self.future_trade_xbtusd(msgdict['price'], msgdict['amount'],'cl',bool(msgdict['islimit']),clientID = msgdict['cid'])
            savestr = 'cl,price:%.1f,amount:%d,islimit:%d,bc:'%(msgdict['price'],msgdict['amount'],msgdict['islimit']) + str(bcmsg)
            self.testTradeSave(savestr)
            print(savestr)
        elif msgdict['type'] == 'os':#open short
            if self.isTest:
                bcmsg = '{"type":"bimex_test_os"}'
            else:
                bcmsg = self.future_trade_xbtusd(msgdict['price'], msgdict['amount'],'os',bool(msgdict['islimit']),clientID = msgdict['cid'])
            savestr = 'os,price:%.1f,amount:%d,islimit:%d,bc:'%(msgdict['price'],msgdict['amount'],msgdict['islimit']) + str(bcmsg)
            self.testTradeSave(savestr)
            print(savestr)
        elif msgdict['type'] == 'cs':#close short
            if self.isTest:
                bcmsg = '{"type":"bimex_test_cs"}'
            else:
                bcmsg = self.future_trade_xbtusd(msgdict['price'], msgdict['amount'],'cs',bool(msgdict['islimit']),clientID = msgdict['cid'])
            savestr = 'os,price:%.1f,amount:%d,islimit:%d,bc:'%(msgdict['price'],msgdict['amount'],msgdict['islimit']) + str(bcmsg)
            self.testTradeSave(savestr)
            print(savestr)
        elif msgdict['type'] == 'getall':
            bcmsg = self.future_orderinfo()
        elif msgdict['type'] == 'getID':
            bcmsg = self.future_orderinfo(orderID = msgdict['id'])
        elif msgdict['type'] == 'cancelall':
            bcmsg = self.future_cancel(orderId = '')
        elif msgdict['type'] == 'cancel':
            bcmsg = self.future_cancel(orderId = msgdict['id'])
        elif msgdict['type'] == 'account':
            bcmsg = self.future_userinfo()
        elif msgdict['type'] == 'withdraw':
            pass
        elif msgdict['type'] == 'transfer':
            pass
        elif msgdict['type'] == 'funding':
            bcmsg = self.future_funding()
        elif msgdict['type'] == 'test':
            self.isTest = bool(msgdict['test'])
            bcmsg = '{"bitmex_etTest":%d}'%(self.isTest)
        print(bcmsg)
        self.sendMsgToClient(bcmsg)
        return

    def timeconvent(self,utcstrtime):
        timest = timetool.utcStrTimeToTime(utcstrtime)
        timeint = int(timest)
        ltimeStr = str(timetool.timestamp2datetime(timeint,True))   
        return timeint,ltimeStr 

    def conventTimeWithList(self,datas):
        outs = []
        for d in datas:
            tmpdic = {}
            for k in d.keys():
                if type(d[k]) == datetime.datetime:
                        tmpdic[k] = int(d[k].timestamp())
                else:
                    tmpdic[k] = d[k]
            outs.append(tmpdic)
        return outs

    #获取最近5次的持仓费率
    def future_funding(self):
        #https://www.bitmex.com/api/v1/funding?count=5&reverse=true
        res = self.client.Funding.Funding_get(filter = '{"symbol":"%s"}'%(self.mType),count = 5,reverse = True).result()
        outdatas = self.conventTimeWithList(res[0])
        return outdatas
    #期货全仓账户信息

    def conventTimeWithDict(self,d):
        tmpdic = {}
        for k in d.keys():
            if type(d[k]) == datetime.datetime:
                    tmpdic[k] = int(d[k].timestamp())
            else:
                tmpdic[k] = d[k]
        return tmpdic

    def future_userinfo(self):
        res = self.client.User.User_getMargin().result()
        print(res)
        outs = self.conventTimeWithDict(res[0])
        return outs
        #https://www.bitmex.com/api/v1/user/margin?currency=XBt

    #期货取消所有定单订单
    def future_cancel(self,orderId = ''):
        res = None
        if orderId == '' or (not orderId):
            res = self.client.Order.Order_cancelAll().result()[0]
            print(res)
        else:
            res = self.client.Order.Order_cancel(clOrdID = orderId).result()[0]
            print(res)
        if res:
            outs = self.conventTimeWithDict(res[0])
            return outs
        else:
            return res

    #期货获取所有订单信息,或者某一个定单信息
    def future_orderinfo(self,orderID = ''):
        # https://www.bitmex.com/api/v1/order?filter=%7B%22symbol%22%3A%20%22XBTUSD%22%7D&count=100&reverse=true
        #获取最后10定单，有成交的也有没有成交的
        if orderID == '':
            res = self.client.Order.Order_getOrders(filter = '{"symbol": "%s"}'%(self.mType),count = 5,reverse = True).result()
            # [{'orderID': '7c6ca135-52e3-6ecb-6b93-5e6edf914f97', 'clOrdID': '', 'clOrdLinkID': '', 'account': 278343, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 100, 'price': 6285.0, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': 'Close', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'New', 'triggered': '', 'workingIndicator': True, 'ordRejReason': '', 'simpleLeavesQty': 0.0159, 'leavesQty': 100, 'simpleCumQty': 0.0, 'cumQty': 0, 'avgPx': None, 'multiLegReportingType': 'SingleSecurity', 'text': 'Position Close from www.bitmex.com', 'transactTime': datetime.datetime(2018, 8, 12, 18, 53, 15, 872000, tzinfo=tzutc()), 'timestamp': datetime.datetime(2018, 8, 12, 18, 53, 15, 872000, tzinfo=tzutc())}, {'orderID': '5ecdab76-6324-64f0-58a9-f41b7e05af3e', 'clOrdID': '', 'clOrdLinkID': '', 'account': 278343, 'symbol': 'XBTUSD', 'side': 'Sell', 'simpleOrderQty': None, 'orderQty': 100, 'price': 6295.0, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': 'ParticipateDoNotInitiate', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': 0.0, 'leavesQty': 0, 'simpleCumQty': 0.015886, 'cumQty': 100, 'avgPx': 6295.0, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submitted via API.', 'transactTime': datetime.datetime(2018, 8, 12, 18, 46, 13, 593000, tzinfo=tzutc()), 'timestamp': datetime.datetime(2018, 8, 12, 18, 49, 47, 302000, tzinfo=tzutc())}, {'orderID': '87adcf6b-e22c-34d8-4902-242a24b9ba02', 'clOrdID': '', 'clOrdLinkID': '', 'account': 278343, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 600, 'price': 5800.0, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'New', 'triggered': '', 'workingIndicator': True, 'ordRejReason': '', 'simpleLeavesQty': 0.0953, 'leavesQty': 600, 'simpleCumQty': 0.0, 'cumQty': 0, 'avgPx': None, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'transactTime': datetime.datetime(2018, 8, 10, 23, 8, 56, 18000, tzinfo=tzutc()), 'timestamp': datetime.datetime(2018, 8, 12, 18, 50, 0, 904000, tzinfo=tzutc())}, {'orderID': 'c3b4fff9-960e-8c2e-86c4-7264e111046d', 'clOrdID': '', 'clOrdLinkID': '', 'account': 278343, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 300, 'price': 6120.0, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': 0.0, 'leavesQty': 0, 'simpleCumQty': 0.04902, 'cumQty': 300, 'avgPx': 6120.0, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'transactTime': datetime.datetime(2018, 8, 9, 22, 13, 11, 424000, tzinfo=tzutc()), 'timestamp': datetime.datetime(2018, 8, 10, 20, 49, 54, 809000, tzinfo=tzutc())}, {'orderID': '370a0683-e566-d21f-5ec8-0b77a26d7615', 'clOrdID': '', 'clOrdLinkID': '', 'account': 278343, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 300, 'price': 6400.0, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': 0.0, 'leavesQty': 0, 'simpleCumQty': 0.046875, 'cumQty': 300, 'avgPx': 6400.0, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'transactTime': datetime.datetime(2018, 8, 8, 9, 52, 27, 568000, tzinfo=tzutc()), 'timestamp': datetime.datetime(2018, 8, 8, 16, 38, 28, 731000, tzinfo=tzutc())}, {'orderID': 'd75b92ac-42a6-e43f-d919-ddd57a97af2b', 'clOrdID': '', 'clOrdLinkID': '', 'account': 278343, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 1000, 'price': 6520.0, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': 'Close', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': 0.0, 'leavesQty': 0, 'simpleCumQty': 0.15188, 'cumQty': 1000, 'avgPx': 6520.0, 'multiLegReportingType': 'SingleSecurity', 'text': 'Position Close from www.bitmex.com', 'transactTime': datetime.datetime(2018, 8, 8, 0, 34, 55, 929000, tzinfo=tzutc()), 'timestamp': datetime.datetime(2018, 8, 8, 4, 8, 45, 692000, tzinfo=tzutc())}, {'orderID': 'e271b60c-3271-9c1e-e72a-285547b1ac7e', 'clOrdID': '', 'clOrdLinkID': '', 'account': 278343, 'symbol': 'XBTUSD', 'side': 'Sell', 'simpleOrderQty': None, 'orderQty': 1000, 'price': 6584.0, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': 0.0, 'leavesQty': 0, 'simpleCumQty': 0.15188, 'cumQty': 1000, 'avgPx': 6584.0, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'transactTime': datetime.datetime(2018, 8, 8, 0, 28, 55, 748000, tzinfo=tzutc()), 'timestamp': datetime.datetime(2018, 8, 8, 0, 32, 47, 199000, tzinfo=tzutc())}, {'orderID': '206d8fe5-ca0f-81a5-1949-67f326b29b22', 'clOrdID': '', 'clOrdLinkID': '', 'account': 278343, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 1000, 'price': 6550.0, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': 'Close', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': 0.0, 'leavesQty': 0, 'simpleCumQty': 0.14131, 'cumQty': 1000, 'avgPx': 6550.0, 'multiLegReportingType': 'SingleSecurity', 'text': 'Position Close from www.bitmex.com', 'transactTime': datetime.datetime(2018, 8, 7, 21, 10, 29, 501000, tzinfo=tzutc()), 'timestamp': datetime.datetime(2018, 8, 8, 0, 12, 58, 809000, tzinfo=tzutc())}, {'orderID': '03928647-56b7-d6c0-faf6-1ea07abc15f9', 'clOrdID': '', 'clOrdLinkID': '', 'account': 278343, 'symbol': 'XBTUSD', 'side': 'Sell', 'simpleOrderQty': None, 'orderQty': 1000, 'price': 7076.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': 0.0, 'leavesQty': 0, 'simpleCumQty': 0.14131, 'cumQty': 1000, 'avgPx': 7076.5, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'transactTime': datetime.datetime(2018, 8, 7, 12, 27, 55, 899000, tzinfo=tzutc()), 'timestamp': datetime.datetime(2018, 8, 7, 12, 29, 11, 611000, tzinfo=tzutc())}, {'orderID': '5157726e-5091-75e1-fb60-4a875918889c', 'clOrdID': '', 'clOrdLinkID': '', 'account': 278343, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 1000, 'price': 6850.0, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': 'Close', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': 0.0, 'leavesQty': 0, 'simpleCumQty': 0.13297, 'cumQty': 1000, 'avgPx': 6850.0, 'multiLegReportingType': 'SingleSecurity', 'text': 'Position Close from www.bitmex.com', 'transactTime': datetime.datetime(2018, 8, 4, 16, 39, 27, 590000, tzinfo=tzutc()), 'timestamp': datetime.datetime(2018, 8, 6, 21, 16, 43, 546000, tzinfo=tzutc())}]
            dep = self.conventTimeWithList(res[0])
            return dep
        else:
            res = self.client.Order.Order_getOrders(filter = '{"symbol":"%s","orderID": "%s"}'%(self.mType,orderID),count = 10,reverse = True).result()
            print(res)
            dep = self.conventTimeWithList(res[0])
            return dep
  #       [{
  #   "orderID": "87adcf6b-e22c-34d8-4902-242a24b9ba02",   #定单ID,
  #   "clOrdID": "",                                        #定单用户定义ID
  #   "clOrdLinkID": "",
  #   "account": 278343,
  #   "symbol": "XBTUSD",
  #   "side": "Buy",                                        #定单开单方向
  #   "simpleOrderQty": null,
  #   "orderQty": 600,                                      #定单委托数量
  #   "price": 5800,
  #   "displayQty": null,
  #   "stopPx": null,
  #   "pegOffsetValue": null,
  #   "pegPriceType": "",
  #   "currency": "USD",
  #   "settlCurrency": "XBt",
  #   "ordType": "Limit",        #定单类型
  #   "timeInForce": "GoodTillCancel",
  #   "execInst": "",
  #   "contingencyType": "",
  #   "exDestination": "XBME",
  #   "ordStatus": "New",        #定单状态，Filled:完全成交,New:未成交
  #   "triggered": "",
  #   "workingIndicator": true,                         #是否有效定单
  #   "ordRejReason": "",
  #   "simpleLeavesQty": 0.1034,  #委托价值
  #   "leavesQty": 600,           #未成交委托数量
  #   "simpleCumQty": 0,
  #   "cumQty": 0,
  #   "avgPx": null,
  #   "multiLegReportingType": "SingleSecurity",
  #   "text": "Submission from www.bitmex.com",
  #   "transactTime": "2018-08-10T23:08:56.018Z",
  #   "timestamp": "2018-08-10T23:08:56.018Z"
  # },{}]
    

    def testTradeSave(self,out):
        f = open('testtrade.txt','a')
        outstr = out + '\n'
        f.write(outstr)
        f.close()
    #xbtusd期货下单
    def future_trade_xbtusd(self,price,amount,tradeType,postOnly,clientID):
    # bitmex的被动下单方式:
    # 设置order的execInst参数为ParticipateDoNotInitiate，当下单价格为主动成交时，下单会被取消
    # ParticipateDoNotInitiate: Also known as a Post-Only order. 
    # If this order would have executed on placement, it will cancel instead.
        res = None
        tmpprice = '%.1f'%(float(price))
        # postOnly = not islimit
        # print('-----------------------')
        # print(self.client.Order.__dict__)
        # print(dir(self.client.Order))
        cID = clientID
        if cID == '' or cID == None:
            self.baseCID += 1
            cID = tradeType + '-' + str(self.baseCID) + '-' + str(int(time.time()))

        if tradeType == 'ol': #开多
            
            if postOnly:
                print('被动开多:'.encode(),tmpprice,amount)
                res = self.client.Order.Order_new(symbol=self.mType, orderQty=int(amount),clOrdID = cID,execInst='ParticipateDoNotInitiate', price=float(tmpprice)).result()
            else:
                print('开多:'.encode(),tmpprice,amount)
                res = self.client.Order.Order_new(symbol=self.mType, orderQty=int(amount),clOrdID = cID, price=float(tmpprice)).result()
        elif tradeType == 'cl': #平多
            
            if postOnly:
                print('被动平多:'.encode(),tmpprice,amount)
                res = self.client.Order.Order_new(symbol=self.mType, orderQty=-int(amount),clOrdID = cID,execInst='ParticipateDoNotInitiate', price=float(tmpprice)).result()
            else:
                print('平多:'.encode(),tmpprice,amount)
                res = self.client.Order.Order_new(symbol=self.mType, orderQty=-int(amount),clOrdID = cID,execInst='Close', price=float(tmpprice)).result()
        elif tradeType == 'os': #开空
            
            if postOnly:
                print('被动开空:'.encode(),tmpprice,amount)
                res = self.client.Order.Order_new(symbol=self.mType, orderQty=-int(amount),clOrdID = cID,execInst='ParticipateDoNotInitiate', price=float(tmpprice)).result()
            else:
                print('开空:'.encode(),tmpprice,amount)
                res = self.client.Order.Order_new(symbol=self.mType, orderQty=-int(amount),clOrdID = cID, price=float(tmpprice)).result()
        elif tradeType == 'cs': #平空
            
            if postOnly:
                print('被动平空:'.encode(),tmpprice,amount)
                res = self.client.Order.Order_new(symbol=self.mType, orderQty=int(amount),clOrdID = cID,execInst='ParticipateDoNotInitiate', price=float(tmpprice)).result()
            else:
                print('平空:',tmpprice,amount)
                res = self.client.Order.Order_new(symbol=self.mType, orderQty=int(amount),clOrdID = cID,execInst='Close', price=float(tmpprice)).result()
        else:
            print('tradeType,下单类型设置错误:'.encode(),tradeType)

        outs = self.conventTimeWithDict(res[0])
        return outs

    #OKCoin期货市场深度信息
    # def future_depth(self,size = 2,symbol = 'XBT',contractType = self.mType): 
    #     if symbol == 'XBT':
    #         if contractType == 'XBTUSD':
    #             #https://www.bitmex.com/api/v1/orderBook/L2?symbol=xbt&depth=2
    #             res = self.client.OrderBook.OrderBook_getL2(symbol=symbol,depth=size).result()
    #             return res[0]
    #         else:
    #             print('合约交易类型%s不可用:'%(contractType))

    #     else:
    #         print('市场类型%s不可用:'%(symbol))

        # return None
    
    


    #OKCoin期货交易记录信息
    def future_trades(self,symbol,contractType):
        pass
        # FUTURE_TRADES_RESOURCE = "/api/v1/future_trades.do"
        # params = ''
        # if symbol:
        #     params += '&symbol=' + symbol if params else 'symbol=' +symbol
        # if contractType:
        #     params += '&contract_type=' + contractType if params else 'contract_type=' +symbol
        # return httpGet(self.__url,FUTURE_TRADES_RESOURCE,params)


    #获取美元人民币汇率
    def exchange_rate(self):
        pass
        # EXCHANGE_RATE = "/api/v1/exchange_rate.do"
        # return httpGet(self.__url,EXCHANGE_RATE,'')


    


    #期货全仓持仓信息
    def future_position(self,symbol,contractType):
        pass
        # FUTURE_POSITION = "/api/v1/future_position.do?"
        # params = {
        #     'api_key':self.__apikey,
        #     'symbol':symbol,
        #     'contract_type':contractType
        # }
        # params['sign'] = buildMySign(params,self.__secretkey)
        # return httpPost(self.__url,FUTURE_POSITION,params)


    #期货批量下单
    def future_batchTrade(self,symbol,contractType,orders_data,leverRate):
        pass
        # FUTURE_BATCH_TRADE = "/api/v1/future_batch_trade.do?"
        # params = {
        #     'api_key':self.__apikey,
        #     'symbol':symbol,
        #     'contract_type':contractType,
        #     'orders_data':orders_data,
        #     'lever_rate':leverRate
        # }
        # params['sign'] = buildMySign(params,self.__secretkey)
        # return httpPost(self.__url,FUTURE_BATCH_TRADE,params)

def main():
    import os,sys

    from sys import version_info  

    if version_info.major < 3:
        import SocketServer as socketserver
        magetoolpth = '/usr/local/lib/python2.7/site-packages'
        if magetoolpth not in sys.path:
            sys.path.append(magetoolpth)
        else:
            print('heave magetool pth')
    else:
        import socketserver

    import socket
    import json

    from magetool import pathtool

    nfpth = os.path.abspath(__file__)
    ndir,_ = os.path.split(nfpth)
    pdir = pathtool.GetParentPath(ndir)
    ppdir = pathtool.GetParentPath(pdir) + os.sep + 'util'
    sys.path.append(ppdir)
    import apikeytool


    apikey = apikeytool.apikeydic['bitmex']['apikey']
    secretkey = apikeytool.apikeydic['bitmex']['secretkey']
    isTest =  bool(apikeytool.apikeydic['isTest'])
    futuretool = BitMexFuture(apikey,secretkey,isTest = True)
    dep = futuretool.future_funding()
    print(type(dep[0]['fundingInterval']))
    print(dep[0]['fundingInterval'])
    if type(dep[0]['fundingInterval']) == datetime.datetime:
        print('dddd---------------------')


    # [{
#   'orderID': '7c6ca135-52e3-6ecb-6b93-5e6edf914f97',
#   'clOrdID': '',
#   'clOrdLinkID': '',
#   'account': 278343,
#   'symbol': 'XBTUSD',
#   'side': 'Buy',
#   'simpleOrderQty': None,
#   'orderQty': 100,
#   'price': 6285.0,
#   'displayQty': None,
#   'stopPx': None,
#   'pegOffsetValue': None,
#   'pegPriceType': '',
#   'currency': 'USD',
#   'settlCurrency': 'XBt',
#   'ordType': 'Limit',
#   'timeInForce': 'GoodTillCancel',
#   'execInst': 'Close',
#   'contingencyType': '',
#   'exDestination': 'XBME',
#   'ordStatus': 'Canceled',
#   'triggered': '',
#   'workingIndicator': False,
#   'ordRejReason': '',
#   'simpleLeavesQty': 0.0,
#   'leavesQty': 0,
#   'simpleCumQty': 0.0,
#   'cumQty': 0,
#   'avgPx': None,
#   'multiLegReportingType': 'SingleSecurity',
#   'text': 'Canceled: Position is in liquidation\nPosition Close from www.bitmex.com',
#   'transactTime': datetime.datetime(2018,
#   8,
#   12,
#   18,
#   53,
#   15,
#   872000,
#   tzinfo=tzutc()),
#   'timestamp': datetime.datetime(2018,
#   8,
#   12,
#   19,
#   26,
#   9,
#   577000,
#   tzinfo=tzutc())
# },
#{}]
if __name__ == '__main__':
    main()





    
