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

from magetool import pathtool
from magetool import timetool
sys.path.append('marketXBTU18_okex/util')
import signTool
# import apikeytool

import platform
import base64

def getSysType():
    sysSystem = platform.system()
    if sysSystem == 'Windows':  #mac系统
        return 'win'
    elif sysSystem == 'Darwin':
        return 'mac'
    elif sysSystem == 'Linux':
        return 'linux'

#语音播报
def sayMsg(msg):
    smsg = msg
    # print smsg
    if getSysType() == 'mac':
        def sayTradeRun():
            cmd = '/usr/bin/say %s'%(smsg)
            os.system(cmd)
        sTradethr = threading.Thread(target=sayTradeRun,args=())
        sTradethr.setDaemon(True)
        sTradethr.start()
    
def getCOnfig():
    f = open('/Users/mage/Documents/btc/okexapikey/okexapikey.txt','r')
    tmpstr = f.read()
    f.close()

    apikeydic = json.loads(tmpstr)
    return apikeydic

class RemoteClient(object):
    """docstring for ClassName"""
    def __init__(self):
        #期货交易工具
        self.configdic = getCOnfig()      #本地签名配置和服务器端口配置

        self.serverport = self.configdic['mport']



        self.tradeConfig = None         #交易下单设置内容

        self.sigenkey = self.configdic['clientkey']          #服务器交互验证身分签名

        self.mSocket = None             #管理服务器socket
        self.mthr = None                #服务器数据接收线程

        self.isconnect = False
        self.initSocket()


    def getConfig(self):
        pass

    def initSocket(self):
        self.initAnalyseServer()
    
    def initAnalyseServer(self):
        isErro = False
        try:
            print('connect magner server:','serverAddr',self.serverport)
            self.mSocket = socket.socket()  # instantiate
            self.mSocket.connect(('flkf.hockshop.xyz', self.serverport))  # connect to the server
            print('magner server connected!')
            def okexTradeRun():
                while True:
                    data = self.mSocket.recv(100*1024)
                    isOK = False
                    datadic = {}
                    try:
                        if data == 'ok':
                            self.isConnectOK()
                        else:
                            datadic = json.loads(data.decode())
                            isOK = True
                    except Exception as e:
                        # print(e)
                        # print(data)
                        if len(data) < 1:
                            self.isOkexTradeOK = False
                            self.mSocket = None
                            return
                        else:
                            datastr = str(data.decode())
                            # print(datastr)
                            if datastr.find('}{') != -1:
                                datas = datastr.split('}{')
                                # print(len(datas))
                                for n in range(len(datas)):
                                    d = datas[n]
                                    if n == 0:
                                        dtmp = d + '}'
                                        ddic = json.loads(dtmp)
                                        
                                        self.onServerMsg(ddic)
                                    elif n == len(datas) -1:
                                        dtmp = '{' + d 
                                        ddic = json.loads(dtmp)
                                        self.onServerMsg(ddic)
                                    else:
                                        dtmp = '{' + d  + '}'
                                        ddic = json.loads(dtmp)
                                        self.onServerMsg(ddic)
                                continue
                    if isOK:
                        self.onServerMsg(datadic)
            self.mthr = threading.Thread(target=okexTradeRun,args=())
            self.mthr.setDaemon(True)
            self.mthr.start()
        except Exception as e:
            print('connect okex http trade server erro...')
            self.mSocket = None
            isErro =  True
        return (not isErro)

    def isConnectOK(self):
        self.isconnect = True
        print('connect ok')

    def onServerMsg(self,datadic):
        # {'data':msgtmp,'state':self.tradeState,'isbase64data':True}
        outlog = ''
        if datadic['isbase64data']:
            datstr = base64.b64decode(datadic['data'].encode())
            # print(datstr,datadic['state'])
            outlog = str(datstr) + str(datadic['state'])
        else:
            # print(datadic['data'],datadic['state'])
            outlog = str(datadic['data']) + str(datadic['state'])
        outlog = '\r' + outlog
        sys.stdout.writelines(outlog)
        sys.stdout.flush()
    def connectMangerServer(self):
        msgdic = 'connectMangerServer'
        ptime = int(time.time())
        signstr = signTool.signClientMsg(msgdic, ptime, self.sigenkey)
        senddat = {'data':msgdic,'time':ptime,'sign':signstr}
        sendstr = 'key,' + json.dumps(senddat)
        self.mSocket.send(sendstr.encode())
    #当有客户端30秒没有接收到数据时就发送ping
    def showlog(self):
        self.mSocket.send('olog'.encode())
    def clog(self):
        self.mSocket.send('clog'.encode())
    def closetest(self):
        self.mSocket.send('ct'.encode())
    def opentest(self):
        self.mSocket.send('ot'.encode())
    def openob(self):
        self.mSocket.send('openob'.encode())
    def closeob(self):
        self.mSocket.send('closeob'.encode())
    def openbo(self):
        self.mSocket.send('openbo'.encode())
    def closebo(self):
        self.mSocket.send('closebo'.encode())
    def printc(self):
        self.mSocket.send('print'.encode())
    def cokex(self):
        self.mSocket.send('cokex'.encode())
    def cbitmex(self):
        self.mSocket.send('cbitmex'.encode())
    def okexol(self):
        self.mSocket.send('okexol'.encode())
    def okexcl(self):
        self.mSocket.send('okexcl'.encode())
    def okexos(self):
        self.mSocket.send('okexos'.encode())
    def okexcs(self):
        self.mSocket.send('okexcs'.encode())
    def bitmexol(self):
        self.mSocket.send('bitmexol'.encode())
    def bitmexcl(self):
        self.mSocket.send('bitmexcl'.encode())
    def bitmexos(self):
        self.mSocket.send('bitmexos'.encode())
    def bitmexcs(self):
        self.mSocket.send('bitmexcs'.encode())
    def clear(self):
        self.mSocket.send('clear'.encode())

    def pingAllServer(self,ptimeDelay = 30):
        pass

    def printSet(self):
        pass

def connect():
    apikeydic = getCOnfig()

    msgdic = 'connectMangerServer'
    ptime = int(time.time())
    sigenkey = apikeydic['clientkey'] 
    signstr = signTool.signClientMsg(msgdic, ptime, sigenkey)
    senddat = {'data':msgdic,'time':ptime,'sign':signstr}
    sendstr = 'key,' + json.dumps(senddat)
    print(sendstr)

def mangerWithServer():
    client = RemoteClient()
    client.connectMangerServer()

    if hasattr(__builtins__, 'raw_input'): 
        inputstr = raw_input
    else:
        inputstr = input

    message = inputstr('prompt:')
    print(message)
    while message.lower().strip() != 'bye':
        sendmsg = ''
        if message.lower().strip() == 'olog':
            client.showlog()
        if message.lower().strip() == 'clog':
            client.clog()

        elif message.lower().strip() == 'ct':
            client.closetest()

        elif message.lower().strip() == 'ot':
            client.opentest()
        elif message.lower().strip() == 'oob':
            client.openob()
        elif message.lower().strip() == 'cob':
            client.closeob()
        elif message.lower().strip() == 'obo':
            client.openbo()
        elif message.lower().strip() == 'cbo':
            client.closebo()
        elif message.lower().strip() == 'okexol':
            client.okexol()
        elif message.lower().strip() == 'okexcl':
            client.okexcl()
        elif message.lower().strip() == 'okexos':
            client.okexos()
        elif message.lower().strip() == 'okexcs':
            client.okexcs()
        elif message.lower().strip() == 'cokex':
            client.cokex()
        elif message.lower().strip() == 'bitmexol':
            client.bitmexol()
        elif message.lower().strip() == 'bitmexcl':
            client.bitmexcl()
        elif message.lower().strip() == 'bitmexos':
            client.bitmexos()
        elif message.lower().strip() == 'bitmexcs':
            client.bitmexcs()
        elif message.lower().strip() == 'cbitmex':
            client.cbitmex()
        elif message.lower().strip() == 'print':
            client.printc()
        elif message.lower().strip() == 'clear':
            client.clear()
        else:
            message = inputstr(" -> ")  # again take input
            continue

def main():
    # connect()
    mangerWithServer()

if __name__ == '__main__':
    main()
   
