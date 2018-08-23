#!/usr/bin/python
# -*- coding: utf-8 -*-
#用于访问OKCOIN 期货REST API
from HttpMD5Util import buildMySign,httpGet,httpPost
import json
import socket
import threading

class OKFuture:
    def __init__(self,secretkey,isTest = True):
        self.__url = ''
        self.__apikey = None
        self.__secretkey = None
        self.secretkey = secretkey
        self.csocket = None
        self.isTest = isTest
        self.objname = 'okex'


        self.testSocket = None
        
        self.okexTradethr = None

        self.initDataSocket()

    def initDataSocket(self):
        isErro = False
        try:
        # if True:
            print('connecting okex http trade server:','127.0.0.1',9898)
            self.testSocket = socket.socket()  # instantiate
            self.testSocket.connect(('127.0.0.1', 9898))  # connect to the server
            print('okex http trade server connected!')
            def okexTradeRun():
                while True:
                    data = self.testSocket.recv(100*1024)
                    print('recive data len:%d'%(len(data)))
                    print(data)
            self.okexTradethr = threading.Thread(target=okexTradeRun,args=())
            self.okexTradethr.setDaemon(True)
            self.okexTradethr.start()
        except Exception as e:
            print('connect okex http trade server erro...')
            self.testSocket = None
            isErro =  True
        return (not isErro)

    def sendMsgToTestDataSocket(self,msg):
        try:
        # if True:
            if self.testSocket:
                outstr = json.dumps(msg)
                self.testSocket.send(outstr.encode())
                return True
            else:
                print('没有数据测试服务器')
                return False
        except Exception as e:
            print('服务器端okexDataSocket网络错误1')
            return False

    def setObjName(self,pname):
        self.objname = pname

    def setSocketClient(self,clientSocket):
        self.csocket = clientSocket

    def saveLog(self,msg):
        f = open('oktradelog.txt','a')
        f.write(msg + '\n')
        f.close()

    #期货下单
    def future_trade(self,symbol,contractType,price='',amount='',tradeType='',matchPrice='',leverRate=''):
        msg = {'type':tradeType,'price':float(price),'amount':int(amount),'cid':'1270246017934336'}
        print('期货下单')
        self.sendMsgToTestDataSocket(msg)
        return ""
    #收到数据处理端的下单消息
    def onTradeMsg(self,msgdic):
    
        bcmsg = ''
    #注意事项，okex后边的三个参数说是可有可无，但不填入数值，签名会出错，无法下单
        if msgdic['type'] == 'ol':#开多
            if self.isTest:
                logstr = '测试开多，数量:%d,价格:%.2f,是否限价单:%d'%(msgdic['amount'],msgdic['price'],msgdic['islimit'])
                print(logstr)
                self.saveLog(logstr)
                bcmsg = '{"test":"ol"}'
            else:
                pmatchPrice = '0'
                if msgdic['islimit'] == 0:
                    pmatchPrice = '1' #对手价，即市价下单
                bcmsg = self.future_trade(symbol = 'btc_usd', contractType = 'quarter',price='{:g}'.format(msgdic['price']),amount = str(msgdic['amount']),tradeType = msgdic['type'],matchPrice = pmatchPrice,leverRate='20')
        elif msgdic['type'] == 'cl':#平多
            if self.isTest:
                logstr = '测试平多，数量:%d,价格:%.2f,是否限价单:%d'%(msgdic['amount'],msgdic['price'],msgdic['islimit'])
                print(logstr)
                bcmsg = '{"test":"cl"}'
                self.saveLog(logstr)
            else:
                pmatchPrice = '0'
                if msgdic['islimit'] == 0:
                    pmatchPrice = '1' #对手价，即市价下单
                bcmsg = self.future_trade(symbol = 'btc_usd', contractType = 'quarter',price='{:g}'.format(msgdic['price']),amount = str(msgdic['amount']),tradeType = msgdic['type'],matchPrice = pmatchPrice,leverRate='20')

        elif msgdic['type'] == 'os':#开空
            if self.isTest:
                logstr = '测试开空，数量:%d,价格:%.2f,是否限价单:%d'%(msgdic['amount'],msgdic['price'],msgdic['islimit'])
                print(logstr)
                bcmsg = '{"test":"os"}'
                self.saveLog(logstr)
            else:
                pmatchPrice = '0'
                if msgdic['islimit'] == 0:
                    pmatchPrice = '1' #对手价，即市价下单
                bcmsg = self.future_trade(symbol = 'btc_usd', contractType = 'quarter',price='{:g}'.format(msgdic['price']),amount = str(msgdic['amount']),tradeType = msgdic['type'],matchPrice = pmatchPrice,leverRate='20')

        elif msgdic['type'] == 'cs':#平空
            if self.isTest:
                logstr = '测试平空，数量:%d,价格:%.2f,是否限价单:%d'%(msgdic['amount'],msgdic['price'],msgdic['islimit'])
                print(logstr)
                self.saveLog(logstr)
                bcmsg = '{"test":"cs"}'
            else:
                pmatchPrice = '0'
                if msgdic['islimit'] == 0:
                    pmatchPrice = '1' #对手价，即市价下单
                bcmsg = self.future_trade(symbol = 'btc_usd', contractType = 'quarter',price='{:g}'.format(msgdic['price']),amount = str(msgdic['amount']),tradeType = msgdic['type'],matchPrice = pmatchPrice,leverRate='20')

        elif msgdic['type'] == 'getall':#获取所有未成交定单，这里主要是看还有多少未成交的
            # 获取所有定单状态
            # {type:getall}
            bcmsg = self.future_orderinfo(symbol = 'btc_usd', contractType = 'quarter', orderId = '-1', status = '1', currentPage = '1', pageLength = '20')
            # pass #返回所有未成交定单数据
        elif msgdic['type'] == 'getID':#获取某个定单的状态,这里主要是看看手续费,成交价
            # 使用定单ID获取定单状态
            # {type:getID,id:123456}
            bcmsg = self.future_orderinfo(symbol = 'btc_usd', contractType = 'quarter', orderId = str(msgdic['id']), status = '', currentPage = '1', pageLength = '20')
            # pass #返回请求定单数据
        elif msgdic['type'] == 'cancelall':#取消所有未成交定单
            # pass
            # 取消所有定单
            # {type:cancelall}
            #首先获取所有未成交定单

            if self.isTest:
                bcmsg = '{"test":"okex_cancelAll"}'
            else:
                msg = {'type':'cancel','cid':''}
                self.sendMsgToTestDataSocket(msg)

        elif msgdic['type'] == 'cancel':#取消某个id定单
            # 取消某个定单
            # {type:cancel,id:123456}
            if self.isTest:
                bcmsg = 'test_cancel,id=%s'%(str(msgdic['id']))
            else:
                msg = {'type':'cancel','cid':str(msgdic['id'])}
                self.sendMsgToTestDataSocket(msg)
            # pass
        elif msgdic['type'] == 'account':#获取帐户信息,帐户权益和保证金率,主要是看会不会全仓爆仓
            # pass
            bctmpmsg = self.future_userinfo()
            dicttmp = json.loads(bctmpmsg)
            if dicttmp['result']:
                bcmsg = bctmpmsg
            elif 'error_code' in dicttmp and dicttmp['error_code'] == 20022:
                bcmsg = self.future_userinfo_4fix()

        elif msgdic['type'] == 'withdraw':#提现
            if self.isTest:
                bcmsg = 'test_withdraw'
                print(str(msgdic))
            else:
                pass #合约这里没有提现接口，提现要在现货中调用接口
            # pass
        elif msgdic['type'] == 'transfer':#okex资金划转
            # okex资金划转
            # {type:transfer,amount:数量,from:从那个资金帐户划转,to:划转到那个资金帐户,cointype:btc}
            pass #合约这里没有这个接口，在要现在货中调用
        elif msgdic['type'] == 'test':
            self.isTest = bool(msgdic['test'])
            bcmsg = '{"okex_setTest":%d}'%(self.isTest)
        elif msgdic['type'] == 'funding':#bitmex获取持仓费率,
            pass #okex没有永续合约，所以没有持仓费问题
        print(bcmsg)
        self.sendMsgToClient(bcmsg.encode())
    #期货全仓账户信息
    def future_userinfo(self):
        FUTURE_USERINFO = "/api/v1/future_userinfo.do?"
        params ={}
        params['api_key'] = self.__apikey
        params['sign'] = buildMySign(params,self.__secretkey)
        return httpPost(self.__url,FUTURE_USERINFO,params)

    #期货全仓持仓信息
    def future_position(self,symbol,contractType):
        FUTURE_POSITION = "/api/v1/future_position.do?"
        params = {
            'api_key':self.__apikey,
            'symbol':symbol,
            'contract_type':contractType
        }
        params['sign'] = buildMySign(params,self.__secretkey)
        return httpPost(self.__url,FUTURE_POSITION,params)

    #期货取消订单
    def future_cancel(self,symbol,contractType,orderId):
        FUTURE_CANCEL = "/api/v1/future_cancel.do?"
        params = {
            'api_key':self.__apikey,
            'symbol':symbol,
            'contract_type':contractType,
            'order_id':orderId
        }
        params['sign'] = buildMySign(params,self.__secretkey)
        return httpPost(self.__url,FUTURE_CANCEL,params)

    #期货获取订单信息
    def future_orderinfo(self,symbol,contractType,orderId,status,currentPage,pageLength):
        FUTURE_ORDERINFO = "/api/v1/future_order_info.do?"
        params = {
            'api_key':self.__apikey,
            'symbol':symbol,
            'contract_type':contractType,
            'order_id':orderId,
            'status':status,
            'current_page':currentPage,
            'page_length':pageLength
        }
        params['sign'] = buildMySign(params,self.__secretkey)
        return httpPost(self.__url,FUTURE_ORDERINFO,params)
    

    #向数据处理服务器发送消息
    def sendMsgToClient(self,msg):
        try:
            if self.csocket:
                self.csocket.send(msg.encode())
            else:
                print("没有客户端连接")
        except Exception as e:
            print('客户端网络错误')

    #OKCOIN期货行情信息
    def future_ticker(self,symbol,contractType):
        FUTURE_TICKER_RESOURCE = "/api/v1/future_ticker.do"
        params = ''
        if symbol:
            params += '&symbol=' + symbol if params else 'symbol=' +symbol
        if contractType:
            params += '&contract_type=' + contractType if params else 'contract_type=' +symbol
        return httpGet(self.__url,FUTURE_TICKER_RESOURCE,params)

    #OKCoin期货市场深度信息
    def future_depth(self,symbol,contractType,size): 
        FUTURE_DEPTH_RESOURCE = "/api/v1/future_depth.do"
        params = ''
        if symbol:
            params += '&symbol=' + symbol if params else 'symbol=' +symbol
        if contractType:
            params += '&contract_type=' + contractType if params else 'contract_type=' +symbol
        if size:
            params += '&size=' + size if params else 'size=' + size
        return httpGet(self.__url,FUTURE_DEPTH_RESOURCE,params)

    #OKCoin期货交易记录信息
    def future_trades(self,symbol,contractType):
        FUTURE_TRADES_RESOURCE = "/api/v1/future_trades.do"
        params = ''
        if symbol:
            params += '&symbol=' + symbol if params else 'symbol=' +symbol
        if contractType:
            params += '&contract_type=' + contractType if params else 'contract_type=' +symbol
        return httpGet(self.__url,FUTURE_TRADES_RESOURCE,params)

    #OKCoin期货指数
    def future_index(self,symbol):
        FUTURE_INDEX = "/api/v1/future_index.do"
        params=''
        if symbol:
            params = 'symbol=' +symbol
        return httpGet(self.__url,FUTURE_INDEX,params)

    #获取美元人民币汇率
    def exchange_rate(self):
        EXCHANGE_RATE = "/api/v1/exchange_rate.do"
        return httpGet(self.__url,EXCHANGE_RATE,'')

    #获取预估交割价
    def future_estimated_price(self,symbol):
        FUTURE_ESTIMATED_PRICE = "/api/v1/future_estimated_price.do"
        params=''
        if symbol:
            params = 'symbol=' +symbol
        return httpGet(self.__url,FUTURE_ESTIMATED_PRICE,params)
    
    #期货批量下单
    def future_batchTrade(self,symbol,contractType,orders_data,leverRate):
        FUTURE_BATCH_TRADE = "/api/v1/future_batch_trade.do?"
        params = {
            'api_key':self.__apikey,
            'symbol':symbol,
            'contract_type':contractType,
            'orders_data':orders_data,
            'lever_rate':leverRate
        }
        params['sign'] = buildMySign(params,self.__secretkey)
        return httpPost(self.__url,FUTURE_BATCH_TRADE,params)

    #期货逐仓账户信息
    def future_userinfo_4fix(self):
        FUTURE_INFO_4FIX = "/api/v1/future_userinfo_4fix.do?"
        params = {'api_key':self.__apikey}
        params['sign'] = buildMySign(params,self.__secretkey)
        return httpPost(self.__url,FUTURE_INFO_4FIX,params)

    #期货逐仓持仓信息
    def future_position_4fix(self,symbol,contractType,type1):
        FUTURE_POSITION_4FIX = "/api/v1/future_position_4fix.do?"
        params = {
            'api_key':self.__apikey,
            'symbol':symbol,
            'contract_type':contractType,
            'type':type1
        }
        params['sign'] = buildMySign(params,self.__secretkey)
        return httpPost(self.__url,FUTURE_POSITION_4FIX,params)


def test():
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
    url = apikeytool.apikeydic['okex']['url']
    apikey = apikeytool.apikeydic['okex']['apikey']
    secretkey = apikeytool.apikeydic['okex']['secretkey']
    isTest =  bool(apikeytool.apikeydic['isTest'])

    tradetool = OKFuture(url, apikey, secretkey,isTest)
    tradetool.setObjName('okex')

    bcmsg = tradetool.future_orderinfo(symbol = 'btc_usd', contractType = 'quarter', orderId = '-1', status = '1', currentPage = '1', pageLength = '20')
    print(bcmsg.encode())
    print(type(bcmsg.encode()))
if __name__ == '__main__':
    test()




    
