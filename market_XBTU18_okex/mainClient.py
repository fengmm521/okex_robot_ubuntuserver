#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-05-24 15:13:31
# @Author  : Your Name (you@example.org)
# @Link    : http://example.org
# @Version : $Id$
#创建SocketServerTCP服务器：
import os,sys
import analyseManger
# sys.path.append('util')
# import apikeytool
# import time
# import json
    
#     {
#     "iOkexRate":0.0005,     //okex主动成交费率
#     "pOkexRate":0.0002,     //okex被动成交费率
#     "iBiemexRate":0.00075,  //bitmex主动成交费率
#     "pBiemexRate":-0.00025,  //bitmex被动成交费率
#     "stepPercent":4,        //下单网格价格是全主动成交手续费的倍数
#     "movePercent":0.6,      //网格滑动价格在网络价格的比例
#     "normTime":3,           //基准价格重新计算时间,单位:小时
#     "reconfigTime":60,       //配置文件检测刷新时间，单位:秒
#     "baseAmount":1           //单次下单量
# }

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

import threading
import time


import socket
import json



from magetool import pathtool

nfpth = os.path.abspath(__file__)
ndir,_ = os.path.split(nfpth)
pdir = pathtool.GetParentPath(ndir)
ppdir = pathtool.GetParentPath(pdir) + os.sep + 'util'
sys.path.append(ppdir)
import apikeytool
import signTool

myname = socket.getfqdn(socket.gethostname())
myaddr = socket.gethostbyname(myname)

print('selfip:%s'%(myaddr))
host = str(myaddr)


port = 9919
# host = "127.0.0.1"
host = '172.25.233.226'
addr = (host,port)


tradetool = None


class Servers(socketserver.StreamRequestHandler):
    def handle(self):
        global tradetool
        print('got connection from ',self.client_address)
        while True:
            try:  
                data = self.request.recv(4096)
            except EOFError:  
                print('接收客户端错误，客户端已断开连接,错误码:'.encode('utf-8'))
                print(EOFError )
                break
            except:  
                print('接收客户端错误，客户端已断开连接'.encode('utf-8'))
                break
            if not data: 
                break
            data = data.decode()
            
            if data[:3] == 'key':
                #key,{"data":"asdkflsadjfladskfj","time":123456789,"sign":18273980s9fsdfasdjfi328349}
                datdic = json.loads(data[4:])
                if signTool.isClientSignOK(datdic,apikeytool.apikeydic['clientkey']):
                    tradetool.setClientSocket(self.request)
                    self.request.send('ok'.encode())
                else:
                    self.request.close()
            elif self.request == tradetool.clientSoket:
                tradetool.runClientCMD(data)
            else:
                print('cmd erro.....')
                print(data)
                if len(data) > 1:
                    self.request.close()
            

def startServerThread():
    server = socketserver.ThreadingTCPServer(addr,Servers,bind_and_activate = False)
    server.allow_reuse_address = True   #设置IP地址和端口可以不使用客户端连接等待，并手动绑定服务器地址和端口，手动激活服务器,要不然每一次重启服务器都会出现端口占用的问题
    server.server_bind()
    server.server_activate()
    print('server started:')
    print(addr)
    server.serve_forever()

def start_server():

    thr = threading.Thread(target=startServerThread,args=())
    thr.setDaemon(True)
    thr.start()



def reconfig():
    f = open('tradeconfig.json','r')
    tmpstr = f.read()

    f.close()
    configdic = json.loads(tmpstr)
    return configdic

def main():
    global tradetool
    

    configdic = reconfig()

    tradetool = analyseManger.TradeTool(apikeytool.apikeydic,configdic)
    tradetool.setLogShow(False)
    delaycount = configdic['reconfigTime']

    start_server()

    starttime = time.ctime(int(time.time()))
    f = open('starttime.txt','w')
    f.write(starttime)
    f.close()

    while True:
        
        time.sleep(10)
        tradetool.pingAllServer()
        
        delaycount -= 10
        if delaycount <= 0:
            configdic = reconfig()
            delaycount = configdic['reconfigTime']
            tradetool.initTraddeConfig(configdic)


#测试
if __name__ == '__main__':
    main()
    
    
