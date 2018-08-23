#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
#客户端调用，用于查看API返回结果

import os,sys
from sys import version_info  

if version_info.major < 3:
    magetoolpth = '/usr/local/lib/python2.7/site-packages'
    if magetoolpth not in sys.path:
        sys.path.append(magetoolpth)
    else:
        print('heave magetool pth')

import time
import json

#定单对象

class BitmexOrder(object):
    """docstring for BitmexOrder"""
    def __init__(self, tradeManger,msgdic,market):
        super(BitmexOrder, self).__init__()
        self.orderID = ''              #定单ID
        self.state = -2                   #定单状态，-2:表示未返回下单信息,-1:未完成下单,0:已下单未成交,1:已下单部分成交,2.完成成交
        self.price = msgdic['price']
        self.market = market
        self.amount = msgdic['amount']
        self.orderType = msgdic['type']          #ol,开多，cl,平多，os，开空,cs,平空
        self.islimit = msgdic['islimit']              #是否限价单
        self.tradeManger = tradeManger      #下单管理器
        
        self.msgdic = msgdic

        self.createTime = int(time.time())  #定单创建时间

        self.TradeSocket = None             #下单操作服务器socket

        self.realPrice = 0.0                #实际成交价

        self.opensubprice = 0.0             #开单时要求价格差的极值,正值表示价格要求差值越大越好，负值表示差值越小越好，
        self.subType = ''                   #'ob':bitmex大于okex,'bo':biemtx小于okex,'cob':平仓ob,'cbo':平仓bo,coball,平仓所有ob,cboall,平仓所有bo


        self.cancelType = 0                 #0表示没有取消定单操作,1,表示正在取消定单，2,表示取消定单完成

        self.isResetOrder = False

    def initSubOrder(self,opensubprice,subtype):
        self.opensubprice = opensubprice
        self.subType = subType

    #设置定单的下单服务socket
    def setTradeSocket(self,pSocket):
        self.TradeSocket = pSocket

    #取消定单
    def cancelOrder(self):
        if self.orderID != '' and self.state < 2 and self.cancelType == 0:
            self.cancelType = 1
            self.tradeManger.cancelOneTrade(self.market,self.orderID)

    #定单状态有更新时调用
    def updateTradeState(self,data):
        #当定单取消成功后，查看现在的差价
        deep = []
        if self.market == 'okex':
            deep = self.tradeManger.okexDatas             #买一价，卖一价，接收数据时间
        elif self.market =='bitmex':
            deep = self.tradeManger.bitmexDatas           #买一价，卖一价，接收数据时间

        pass #如果定单成交，不理会

        #如果定单是取消，则看是否是重制定单的取消定单,是则重新下单
        if self.isResetOrder:
            self.tradeManger.okexTradeMsgs.pop()
            if self.subType == 'ob':
                steprice = (self.tradeManger.bitmexDatas[1][0] * self.tradeManger.stepPercent)*((1+self.tradeManger.stepPercent)^(1+len(self.tradeManger.obsubs)))
                self.tradeManger.openOB(steprice,isReset = True)
            elif self.subType == 'bo':
                steprice = (self.tradeManger.okexDatas[1][0] * self.tradeManger.stepPercent)*((1+self.tradeManger.stepPercent)^(1+len(self.tradeManger.obsubs)))
                self.tradeManger.openBO(steprice,isReset = True)
            elif self.subType == 'cob':
                steprice = (self.tradeManger.bitmexDatas[1][0] * self.tradeManger.stepPercent)
                self.tradeManger.closeOB(steprice,isReset = True)
            elif self.subType == 'cbo':
                steprice = (self.tradeManger.okexDatas[1][0] * self.tradeManger.stepPercent)
                self.tradeManger.closeOB(steprice,isReset = True)
            elif self.subType == 'coball':
                steprice = (self.tradeManger.bitmexDatas[1][0] * self.tradeManger.stepPercent)
                self.tradeManger.closeOB(steprice,closeAll = True)
            elif self.subType == 'cboall':
                steprice = (self.tradeManger.okexDatas[1][0] * self.tradeManger.stepPercent)
                self.tradeManger.closeOB(steprice,closeAll = True)

    #重新下单
    def reSetOrder(self):
        self.cancelOrder()   #先取消之前的定单
        self.isResetOrder = True


    #市场深度更新后调用的方法
    def updateMarketDeep(self):
        deep = []
        if self.market == 'okex':
            deep = self.tradeManger.okexDatas             #买一价，卖一价，接收数据时间
        elif self.market =='bitmex':
            deep = self.tradeManger.bitmexDatas           #买一价，卖一价，接收数据时间
        buyprice = deep[0][0]                 #买一价
        sellprice = deep[1][0]                #卖一价
        if self.state == 0: #已下单未成交,这时判断是否要取消定单再重新下单
            if self.orderType == 'ol' or self.orderType == 'cs':#开多或平空时，定单为买入单
                if self.opensubprice > 0 and buyprice - self.price >= 5 and (self.tradeManger.okexDatas[0][0] - self.tradeManger.bitmexDatas[1][0]) > self.opensubprice + 2:#要求买入差价越大越好
                    self.reSetOrder()
                elif self.opensubprice > 0 and (self.tradeManger.okexDatas[0][0] - self.tradeManger.bitmexDatas[1][0]) < self.opensubprice - 2:
                    self.cancelOrder()
                elif self.opensubprice <= 0 and buyprice - self.price >= 5 and (self.tradeManger.okexDatas[1][0] - self.tradeManger.bitmexDatas[0][0]) > self.opensubprice + 2:
                    self.reSetOrder()
                elif self.opensubprice <= 0 and self.tradeManger.okexDatas[1][0] - self.tradeManger.bitmexDatas[0][0] < self.opensubprice - 2:
                    self.cancelOrder()
            elif self.orderType == 'os' or self.orderType == 'cl':
                if self.opensubprice > 0 and self.price - sellprice >= 5 and (self.tradeManger.okexDatas[0][0] - self.tradeManger.bitmexDatas[1][0]) > self.opensubprice + 2:
                    self.cancelOrder()
                elif self.opensubprice > 0 and (self.tradeManger.okexDatas[0][0] - self.tradeManger.bitmexDatas[1][0]) < self.opensubprice - 2:
                    self.reSetOrder()
                elif self.opensubprice <= 0 and buyprice - self.price >= 5 and (self.tradeManger.okexDatas[1][0] - self.tradeManger.bitmexDatas[0][0]) > self.opensubprice + 2:
                    self.cancelOrder()
                elif self.opensubprice <= 0 and self.tradeManger.okexDatas[1][0] - self.tradeManger.bitmexDatas[0][0] < self.opensubprice - 2:
                    self.reSetOrder()



def main():
     pass
if __name__ == '__main__':
    main()
   
