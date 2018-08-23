#!/usr/bin/python
# -*- coding: utf-8 -*-

from HttpMD5Util import buildMySign,httpGet,httpPost
import json

class OKFuture:
    def __init__(self,url,apikey,secretkey,isTest = True):
        self.__url = url
        self.__apikey = apikey
        self.__secretkey = secretkey
        self.secretkey = secretkey
        self.csocket = None
        self.isTest = isTest
        self.objname = 'okex'
    def setObjName(self,pname):
        self.objname = pname

    def setSocketClient(self,clientSocket):
        self.csocket = clientSocket

    def saveLog(self,msg):
        # f = open('oktradelog.txt','a')
        # f.write(msg.encode() + '\n')
        # f.close()
        pass
    #收到数据处理端的下单消息
    def onTradeMsg(self,msgdic):
    # 下单数据格式:
    #设置打开或者关闭测试模式
    #{type:test,test:1}
    

    # 开多,
    # {type:ol,amount:100,price:100,islimit:1,cid:clientorderid}
    # 平多,
    # {type:cl,amount:100,price:100,islimit:1,cid:clientorderid}
    # 开空,
    # {type:os,amount:100,price:100,islimit:1,cid:clientorderid}
    # 平空
    # {type:cs,amount:100,price:100,islimit:1,cid:clientorderid}

    # 获取定单状态
    # 获取所有定单状态
    # {type:getall}
    # 使用定单ID获取定单状态
    # {type:getID,id:123456}
    # 取消某个定单
    # {type:cancel,id:123456}
    # 取消所有定单
    # {type:cancelall}

    # 帐户
    # 获取帐户信息
    # {type:account}
    # 提现
    # {type:withdraw,addr:地址,amount:数量,price:支付手续费,cointype:btc}
    # okex资金划转
    # {type:transfer,amount:数量,from:从那个资金帐户划转,to:划转到那个资金帐户,cointype:btc}
    
        bcmsg = ''
    #注意事项，okex后边的三个参数说是可有可无，但不填入数值，签名会出错，无法下单
        if msgdic['type'] == 'ol':#开多
            if self.isTest:
                logstr = '测试开多，数量:%d,价格:%.2f,是否限价单:%d'%(msgdic['amount'],msgdic['price'],msgdic['islimit'])
                print(logstr.encode())
                self.saveLog(logstr)
                bcmsg = '{"test":"ol"}'
            else:
                pmatchPrice = '0'
                if msgdic['islimit'] == 0:
                    pmatchPrice = '1' #对手价，即市价下单
                bcmsgdata = self.future_trade(symbol = 'btc_usd', contractType = 'quarter',price='{:g}'.format(msgdic['price']),amount = str(msgdic['amount']),tradeType = '1',matchPrice = pmatchPrice,leverRate='20')
                bcmsg = '{"type":"ol","cid":"%s","data":%s}'%(msgdic['cid'],bcmsgdata)
        elif msgdic['type'] == 'cl':#平多
            if self.isTest:
                logstr = '测试平多，数量:%d,价格:%.2f,是否限价单:%d'%(msgdic['amount'],msgdic['price'],msgdic['islimit'])
                print(logstr.encode())
                bcmsg = '{"test":"cl"}'
                self.saveLog(logstr)
            else:
                pmatchPrice = '0'
                if msgdic['islimit'] == 0:
                    pmatchPrice = '1' #对手价，即市价下单
                bcmsgdata = self.future_trade(symbol = 'btc_usd', contractType = 'quarter',price='{:g}'.format(msgdic['price']),amount = str(msgdic['amount']),tradeType = '3',matchPrice = pmatchPrice,leverRate='20')
                bcmsg = '{"type":"cl","cid":"%s","data":%s}'%(msgdic['cid'],bcmsgdata)
        elif msgdic['type'] == 'os':#开空
            if self.isTest:
                logstr = '测试开空，数量:%d,价格:%.2f,是否限价单:%d'%(msgdic['amount'],msgdic['price'],msgdic['islimit'])
                print(logstr.encode())
                bcmsg = '{"test":"os"}'
                self.saveLog(logstr)
            else:
                pmatchPrice = '0'
                if msgdic['islimit'] == 0:
                    pmatchPrice = '1' #对手价，即市价下单
                bcmsgdata = self.future_trade(symbol = 'btc_usd', contractType = 'quarter',price='{:g}'.format(msgdic['price']),amount = str(msgdic['amount']),tradeType = '2',matchPrice = pmatchPrice,leverRate='20')
                bcmsg = '{"type":"os","cid":"%s","data":%s}'%(msgdic['cid'],bcmsgdata)
        elif msgdic['type'] == 'cs':#平空
            if self.isTest:
                logstr = '测试平空，数量:%d,价格:%.2f,是否限价单:%d'%(msgdic['amount'],msgdic['price'],msgdic['islimit'])
                print(logstr.encode())
                self.saveLog(logstr)
                bcmsg = '{"test":"cs"}'
            else:
                pmatchPrice = '0'
                if msgdic['islimit'] == 0:
                    pmatchPrice = '1' #对手价，即市价下单
                bcmsgdata = self.future_trade(symbol = 'btc_usd', contractType = 'quarter',price='{:g}'.format(msgdic['price']),amount = str(msgdic['amount']),tradeType = '4',matchPrice = pmatchPrice,leverRate='20')
                bcmsg = '{"type":"cs","cid":"%s","data":%s}'%(msgdic['cid'],bcmsgdata)
        elif msgdic['type'] == 'getall':#获取所有未成交定单，这里主要是看还有多少未成交的
            # 获取所有定单状态
            # {type:getall}
            bcmsgdata = self.future_orderinfo(symbol = 'btc_usd', contractType = 'quarter', orderId = '-1', status = '1', currentPage = '1', pageLength = '20')
            bcmsg = '{"type":"getall","data":%s}'%(bcmsgdata)
            # pass #返回所有未成交定单数据
        elif msgdic['type'] == 'getID':#获取某个定单的状态,这里主要是看看手续费,成交价
            # 使用定单ID获取定单状态
            # {type:getID,id:123456}
            bcmsgdata = self.future_orderinfo(symbol = 'btc_usd', contractType = 'quarter', orderId = str(msgdic['id']), status = '', currentPage = '1', pageLength = '20')
            bcmsg = '{"type":"getID","oid":"%s","data":%s}'%(str(msgdic['id']),bcmsgdata)
            # pass #返回请求定单数据
        elif msgdic['type'] == 'cancelall':#取消所有未成交定单
            # pass
            # 取消所有定单
            # {type:cancelall}
            #首先获取所有未成交定单
            if self.isTest:
                bcmsg = 'test_cancelall'
            else:
                bcmsgtmp = self.future_orderinfo(symbol = 'btc_usd', contractType = 'quarter', orderId = '-1', status = '1', currentPage = '1', pageLength = '20')
                # pass #返回所有未成交定单数据
                bddic = json.loads(bcmsgtmp)
                if bddic['result'] == True and len(bddic['orders']) > 0:
                    corderids = ''
                    for od in bddic['orders']:
                        corderids += str(od['order_id']) + ','
                    corderids = corderids[:-1]
                    bcmsgdata = self.future_cancel(symbol = 'btc_usd', contractType = 'quarter', orderId = corderids)
                    bcmsg = '{"type":"cancelall","data":%s}'%(bcmsgdata)

        elif msgdic['type'] == 'cancel':#取消某个id定单
            # 取消某个定单
            # {type:cancel,id:123456}
            if self.isTest:
                bcmsg = 'test_cancel,id=%s'%(str(msgdic['id']))
            else:
                bcmsgdata = self.future_cancel(symbol = 'btc_usd', contractType = 'quarter', orderId = str(msgdic['id']))
                bcmsg = '{"type":"cancel","oid":"%s","data":%s}'%(str(msgdic['id']),bcmsgdata)
            # pass
        elif msgdic['type'] == 'account':#获取帐户信息,帐户权益和保证金率,主要是看会不会全仓爆仓
            # pass
            bctmpmsg = self.future_userinfo()
            dicttmp = json.loads(bctmpmsg)
            bcmsgdata = ''
            if dicttmp['result']:
                bcmsgdata = bctmpmsg
            elif 'error_code' in dicttmp and dicttmp['error_code'] == 20022:
                bcmsgdata = self.future_userinfo_4fix()
            bcmsg = '{"type":"account","data":%s}'%(bcmsgdata)

        elif msgdic['type'] == 'pos':
            bctmpmsg = self.future_position(symbol = 'btc_usd', contractType = 'quarter')
            bcmsgdata = ''
            if dicttmp['result']:
                bcmsgdata = bctmpmsg
            elif 'error_code' in dicttmp and dicttmp['error_code'] == 20022:
                bcmsgdata = self.future_position_4fix(symbol = 'btc_usd', contractType = 'quarter', type1 = '1')
            bcmsg = '{"type":"pos","data":%s}'%(bcmsgdata)
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
        self.sendMsgToClient(bcmsg)
    #期货全仓账户信息
    def future_userinfo(self):
        FUTURE_USERINFO = "/api/v1/future_userinfo.do?"
        params ={}
        params['api_key'] = self.__apikey
        params['sign'] = buildMySign(params,self.__secretkey)
        try:
            res = httpPost(self.__url,FUTURE_USERINFO,params)
        except Exception as e:
            res = '{"result":false}'
        return res

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
        
        try:
            res = httpPost(self.__url,FUTURE_CANCEL,params)
        except Exception as e:
            outtype = ''
            res = '{"result":false,"oid":"%s"}'%(orderId)
        return res

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
        
    #期货下单
    def future_trade(self,symbol,contractType,price='',amount='',tradeType='',matchPrice='',leverRate=''):
        FUTURE_TRADE = "/api/v1/future_trade.do?"
        params = {
            'api_key':self.__apikey,
            'symbol':symbol,
            'contract_type':contractType,
            'amount':amount,
            'type':tradeType,
            'match_price':matchPrice,
            'lever_rate':leverRate
        }
        if price:
            params['price'] = price
        params['sign'] = buildMySign(params,self.__secretkey)
        try:
            # {"type":"ol","cid":"sssss","data":{"result":true,"order_id":1304160027118592}}
            res = httpPost(self.__url,FUTURE_TRADE,params)
        except Exception as e:
            print(e)
            outtype = ''
            if tradeType == '1':
                outtype = 'ol'
            elif tradeType == '2':
                outtype = 'os'
            elif tradeType == '3':
                outtype = 'cl'
            elif tradeType == '4':
                outtype = 'cs'
            res = '{"result":false,"orderType":"%s","amount":%s,"price":%s}'%(outtype,amount,price)
        return res

    #向数据处理服务器发送消息
    def sendMsgToClient(self,msg):
        try:
            if self.csocket:
                self.csocket.send(msg.encode())
            else:
                print("not heave client")
        except Exception as e:
            print('client net erro')

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
# buy_amount:多仓数量
# buy_available:多仓可平仓数量 
# buy_bond:多仓保证金
# buy_flatprice:多仓强平价格
# buy_profit_lossratio:多仓盈亏比
# buy_price_avg:开仓平均价
# buy_price_cost:结算基准价
# buy_profit_real:多仓已实现盈余
# contract_id:合约id
# contract_type:合约类型
# create_date:创建日期
# sell_amount:空仓数量
# sell_available:空仓可平仓数量 
# sell_bond:空仓保证金
# sell_flatprice:空仓强平价格
# sell_profit_lossratio:空仓盈亏比
# sell_price_avg:开仓平均价
# sell_price_cost:结算基准价
# sell_profit_real:空仓已实现盈余
# symbol:btc_usd   ltc_usd    eth_usd    etc_usd    bch_usd
# lever_rate: 杠杆倍数
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




    
