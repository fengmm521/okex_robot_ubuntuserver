#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import time
import zlib
import hashlib
import websocket
import json
try:
    import thread
except ImportError:
    import _thread as thread
#okex
#websocket只用来定阅数据推送，下单使用rest的https接口发送

class okWSTool():
    def __init__(self,apikey,secretkey):
        self.wsocket = 0
        self.timeDelay = int(time.time())
        self.api_key = apikey
        self.secret_key = secretkey
        self.url = None

        self.csocket = None


        self.sells = {}
        self.buys = {}
        self.isNotInitDeep = True

        self.sells5 = []
        self.buys5 = []

        #账户余额
        self.btcBalance = 0.0
        self.ltcBalance = 0.0
        self.eosBalance = 0.0
        self.ethBalance = 0.0

        #帐户初始资金，用来计算收益率
        self.baseBTC = 0.0
        self.baseLTC = 0.0
        self.baseEOS = 0.0
        self.baseETH = 0.0

        self.savedatas = []

        self.msgBuffer = []
        self.isWSOpen = False

        self.lastPingTime = int(time.time())

        self.objname = 'okex'

        self.removeSocketFlogFile()

        self.initWebSocket()

        self.sendcount = 100   #每100次log提示一次没有客户端连接

    def removeSocketFlogFile(self):
        if os.path.exists('sokceterro.txt'):
            os.remove('sokceterro.txt')

    def setObjName(self,pname):
        self.objname = pname

    #获取收益率
    def getYield(self,coinType = 'btc'):
        if coinType == 'btc' and self.baseBTC > 0:
            return (self.btcBalance/self.baseBTC)*100   #返百分比收益率
        return 0

    #事件回调函数
    def setSocketClient(self,clientsocket):
        self.csocket = clientsocket

    def sendMsgToClient(self,msg):
        def run(*args):
            try:
                if self.csocket:
                    self.csocket.send(msg.encode())
                else:
                    self.sendcount -= 1
                    if self.sendcount < 0:
                        self.sendcount = 100
                        print("没有客户端连接".encode())
            except Exception as e:
                print('客户端网络错误'.encode())
                if self.csocket:
                    self.csocket.close()
                self.csocket = None
                return
        thread.start_new_thread(run, ())
        
    #收到来自数据处理的命令消息
    def reciveCmdFromClient(self,cmd):
        print(cmd)
        self.sendMsgToClient(str(cmd))

    #有交易数据更新
    def onTrade(self,datadic):
        # [{"binary":0,"channel":"ok_sub_futureusd_trades","data":{"lever_rate":10.0,"amount":1.0,"orderid":1058866628096,"contract_id":201880010015,"fee":0.0,"contract_name":"LTC0928","unit_amount":10.0,"price_avg":0.0,"type":1,"deal_amount":0.0,"contract_type":"quarter","user_id":2051526,"system_type":0,"price":70.0,"create_date_str":"2018-07-07 00:09:37","create_date":1530893377117,"status":0}}]
        print(datadic)
        if type(datadic) == dict:
            msg = json.dumps(datadic)
            self.sendMsgToClient(msg)

    #合约持仓信息更新
    def onPositionsChange(self,datadic):
        #[{"binary":0,"channel":"ok_sub_futureusd_positions","data":{"symbol":"ltc_usd","user_id":2051526,"positions":[{"bondfreez":0.01428571,"margin":0.0,"avgprice":82.005,"eveningup":0.0,"contract_id":201809280015,"hold_amount":0.0,"contract_name":"LTC0928","realized":0.0,"position":1,"costprice":73.499,"position_id":938193331968},{"bondfreez":0.01428571,"margin":0.0,"avgprice":0.0,"eveningup":0.0,"contract_id":201809210015,"hold_amount":0.0,"contract_name":"LTC0928","realized":0.0,"position":2,"costprice":0.0,"position_id":938195331968}]}}]
        print(datadic)
        if type(datadic) == dict:
            msg = json.dumps(datadic)
            self.sendMsgToClient(msg)

    #用户帐户信息更新
    def onUserInfoChange(self,datadic):
        # [{"binary":0,"channel":"ok_sub_futureusd_userinfo","data":{"symbol":"ltc_usd","balance":0.08094866,"unit_amount":10.0,"profit_real":0.0,"keep_deposit":0.01428571}}]
        print(datadic)
        if datadic['symbol'] == 'ltc_usd':
            self.ltcBalance = datadic['balance']
            if self.baseLTC <= 0.0:
                self.baseLTC = datadic['balance']
        elif datadic['symbol'] == 'btc_usd':
            self.btcBalance = datadic['balance']
            if self.baseBTC <= 0.0:
                self.baseBTC = datadic['balance']
        elif datadic['symbol'] == 'eos_usd':
            self.eosBalance = datadic['balance']
            if self.baseEOS <= 0.0:
                self.baseEOS = datadic['balance']
        elif datadic['symbol'] == 'eth_usd':
            self.ethBalance = datadic['balance']
            if self.baseETH <= 0.0:
                self.baseETH = datadic['balance']
        else:
            showlog = '目前未对该币种(%s)作交易统计'%(datadic['symbol'])
            print(showlog.encode())
    def updateDeep(self,datas):
        asks = datas['asks']  #卖
        bids = datas['bids']  #买
        if self.isNotInitDeep:
            for a in asks:
                self.sells[a[0]] = a
            for b in bids:
                self.buys[b[0]] = b
            self.isNotInitDeep = False
        else:
            for a in asks:
                if int(a[1]) == 0:
                    self.sells.pop(a[0])
                else:
                    self.sells[a[0]] = a
            for b in bids:
                if int(b[1]) == 0:
                    self.buys.pop(b[0])
                else:
                    self.buys[b[0]] = b
    #获取市场深度数据
    def getDeeps(self,deepcount = 5):
        sells = list(self.sells.keys())
        buys = list(self.buys.keys())
        sells.sort(reverse = False)
        buys.sort(reverse = True)
        print('-------1--------')
        print(sells[:deepcount])
        print(buys[:deepcount])
        print('-------1end--------')
        sellouts = []
        buyouts = []
        for s in sells[:deepcount]:
            sellouts.append(self.sells[s])
        for b in buys[:deepcount]:
            buyouts.append(self.buys[b])
        return sellouts,buyouts

    def on_open(self,ws):
        self.isWSOpen = True
        # self.openFutureTicker()
        self.openFutureDepth()
        time.sleep(0.1)
        print('open')
        self.onUserLogin()
        msg = '{"type":"socket","state":"open"}'
        self.sendMsgToClient(msg)
        
    def saveDeepList(self):
        out = ''
        for d in self.savedatas:
            out += json.dumps(d) + '\n'
        f = open('okexdeep.txt','a')
        f.write(out)
        f.close()

    def setDeeps(self,datadic):
        self.sells5 = datadic['asks'][::-1]
        self.buys5 = datadic['bids']
        print(self.buys5[0],self.sells5[0])
        self.savedatas.append([int(time.time()),self.buys5,self.sells5])
        if len(self.savedatas) >= 100:
            self.saveDeepList()
            self.savedatas = []

    def on_message(self,ws,data):
        # data = self.inflate(evt) #data decompress
        try:
            self.sendMsgToClient(data)
            datadic = json.loads(data)[0]
            chanle = datadic['channel']
            if chanle == 'ok_sub_futureusd_btc_depth_quarter': #深度增量更新数据
                self.updateDeep(datadic['data'])
                sells,buys = self.getDeeps(3)
                print(sells)
                print(buys)
            elif chanle == 'ok_sub_futureusd_btc_depth_quarter_5':#深度全量数据
                # print(datadic)
                self.setDeeps(datadic['data'])
            elif chanle == 'ok_sub_futureusd_trades':
                #交易数据更新
                self.onTrade(datadic)
            elif chanle == 'ok_sub_futureusd_positions': #合约持仓信息更新
                self.onPositionsChange(datadic)
            elif chanle == 'ok_sub_futureusd_userinfo':  #合约帐户信息更新
                self.onUserInfoChange(datadic)
            else:
                print(data)
        except Exception as e:
            print('-'*20)
            print(data)
        ptime = int(time.time())
        if ptime - self.lastPingTime >= 30:
            self.lastPingTime = ptime
            self.pingServer()

    #有加密时的解密    
    def inflate(self,data):
        decompress = zlib.decompressobj(
                -zlib.MAX_WBITS  # see above
        )
        inflated = decompress.decompress(data)
        inflated += decompress.flush()
        return inflated

    def on_error(self,ws,evt):
        print(evt)

    def on_close(self,ws):
        self.isWSOpen = False
        print('DISCONNECT')
        
        msg = '{"type":"socket","state":"close"}'
        self.sendMsgToClient(msg)
        time.sleep(0.3)
        f = open('sokceterro.txt','w')
        f.write('1')
        f.close()
        time.sleep(10)
        
        # while not self.isWSOpen:
        #     time.sleep(10)
        #     self.initWebSocket()
        #     time.sleep(5)

    #设置客户端websocket
    def initWebSocket(self):
        print('xxx')
        self.url = 'wss://real.okex.com:10440/websocket/okexapi'
        # url = 'wss://47.90.109.236:10440/websocket/okexapi'
        websocket.enableTrace(True)
        self.wsocket = websocket.WebSocketApp(self.url,
                                    on_message = self.on_message,
                                    on_error = self.on_error,
                                    on_close = self.on_close)
        self.wsocket.on_open = self.on_open
        # self.wsocket.run_forever()
    def wsRunForever(self):
        self.wsocket.run_forever()
    #期货收报机数据
    # ① X值为：btc, ltc, eth, etc, bch,eos,xrp,btg 
    # ② Y值为：this_week, next_week, quarter
    def openFutureTicker(self,X = 'btc',Y = 'quarter'):#默认使用季合约#ok_sub_futureusd_X_ticker_Y
        chanelcmd = "{'event':'addChannel','channel':'ok_sub_futureusd_%s_ticker_%s'}"%(X,Y)
        self.wsocket.send(chanelcmd)
    #期货成交数据推送
    # ① X值为：btc, ltc, eth, etc, bch,eos,xrp,btg 
    # ② Y值为：this_week, next_week, quarter
    def openFutureData(self,X = 'btc',Y = 'quarter'):#默使用季合约成交数据
        chanelcmd = "{'event':'addChannel','channel':'ok_sub_futureusd_%s_trade_%s'}"%(X,Y)
        self.wsocket.send(chanelcmd)
    #期货200深度增量数据推送,
    # ① X值为：btc, ltc, eth, etc, bch,eos,xrp,btg 
    # ② Y值为：this_week, next_week, quarter
    def openFutureDepth200(self,X = 'btc',Y = 'quarter'):
        channelcmd = "{'event':'addChannel','channel':'ok_sub_futureusd_%s_depth_%s'}"%(X,Y)
        self.wsocket.send(channelcmd);
    #期货完全深度数据推送,
    # ① X值为：btc, ltc, eth, etc, bch,eos,xrp,btg 
    # ② Y值为：this_week, next_week, quarter 
    # ③ Z值为：5, 10, 20(获取深度条数)
    def openFutureDepth(self,X = 'btc',Y = 'quarter',Z = 5):
        channelcmd = "{'event':'addChannel','channel':'ok_sub_futureusd_%s_depth_%s_%d','binary':1}"%(X,Y,Z)
        self.wsocket.send(channelcmd);
    #订阅合约指数
    # ① X值为：btc, ltc, eth, etc, bch,eos,xrp,btg 
    def openFutureIndex(self,X = 'btc'):
        channelcmd = "{'event':'addChannel','channel':'ok_sub_futureusd_%s_index'}"%(X)
        self.wsocket.send(channelcmd);
    #合约预估交割价格
    # ① X值为：btc, ltc, eth, etc, bch,eos,xrp,btg 
    def openFutureForcast(self,X = 'btc'):
        channelcmd = "{'event':'addChannel','channel':'%s_forecast_price'}"%(X)
        self.wsocket.send(channelcmd);

    #以下为个人事件，需要apikey和sign
    #用户登录事件和个人帐户变动推送
    def onUserLogin(self):
        signstr = self.getLoginSign()
        channelcmd = '''{"event":"login","parameters":{"api_key":"%s","sign":"%s"} }'''%(self.api_key,signstr)
        self.wsocket.send(channelcmd);

    def getLoginSign(self):
        sign = 'api_key=' + str(self.api_key ) + '&secret_key=' + self.secret_key
        return  hashlib.md5((sign).encode("utf-8")).hexdigest().upper()

    #ping服务器查看连接是否断开
    #服务器未断开会返回{"event":"pong"}
    def pingServer(self):
        channelcmd = "{'event':'ping'}"
        self.wsocket.send(channelcmd);


def main():
    oktool = OKFutureWSClient()
    oktool.wsRunForever()
if __name__ == '__main__':
    main()