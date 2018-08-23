#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-12-07 09:28:00
# @Link    : http://fengmm521.blog.163.com
# @Version : $Id$
#https服务器
import os
import ssl
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import threading
import cgi
import time
import posixpath
import urllib
import sys
import shutil
import mimetypes
import json
import base64
import hashlib

import zlib

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

nowPth = os.path.split(os.getcwd())[1]
curdir = '.'

import socket
hostname = socket.gethostname()
selfip = socket.gethostbyname(hostname)

setLastIP = selfip

reload(sys)  
sys.setdefaultencoding('utf8')  

print 'selfIP:',selfip
print 'setLastIP:',setLastIP

#sell1.woodcol.com
from servertool import hardKeysTool
from servertool import regKeysTool
from servertool import UserDBTool
from servertool import AEStool

userdbtoolobj = UserDBTool.UserDBTool()
regKeysToolObj = regKeysTool.RegKeysTool()
hardKeysToolObj = hardKeysTool.hardKeysTool()


def getCreateKey():
    f = open('./keys/create.json','r')
    jstr = f.read()
    f.close()
    dic = json.loads(jstr)
    return dic['key']

createKey = getCreateKey()


def getCodeFromFile(fpth):
    if not os.path.exists(fpth):
        return ''
    else:
        f = open(fpth,'r')
        out = f.read()
        f.close()
        return str(out)

userTrailCode = getCodeFromFile('./downtooltrail.py')

userRegCode = getCodeFromFile('./downtool.py')

userClientToolCode = getCodeFromFile('./clientRegTool.py')

# print(userRegCode)
# print(type(userRegCode))
def getAESCodeTrail(hardID):
    hardIDtmp = hardID + 'code.woodcol.com'
    hexstr = hashlib.sha256(hardIDtmp).hexdigest()
    result = bytearray.fromhex(hexstr)
    aeskey = bytes(result)
    aesobj = AEStool.prpcrypt(aeskey)
    aescode = aesobj.encrypt(userTrailCode)
    b64str = base64.b64encode(aescode)
    return b64str

def getADSCodeRegUser(hardID,regID):
    hardIDtmp = hardID + 'code.woodcol.com' + regID
    print(hardIDtmp)
    hexstr = hashlib.sha256(hardIDtmp).hexdigest()
    result = bytearray.fromhex(hexstr)
    aeskey = bytes(result)
    aesobj = AEStool.prpcrypt(aeskey)
    aescode = aesobj.encrypt(userRegCode)
    b64str = base64.b64encode(aescode)
    return b64str

def getAESClientToolCode(hardID):
    hardIDtmp = hardID + 'clientcode.woodcol.com'
    print(hardIDtmp)
    hexstr = hashlib.sha256(hardIDtmp).hexdigest()
    result = bytearray.fromhex(hexstr)
    aeskey = bytes(result)
    aesobj = AEStool.prpcrypt(aeskey)
    aescode = aesobj.encrypt(userClientToolCode)
    b64str = base64.b64encode(aescode)
    return b64str


class myHandler(BaseHTTPRequestHandler):
    def sendClientRegToolCode(self,hardMsgObj):
        hardID = hardMsgObj['HardID']
        backdic = {}
        backdic['code'] = getAESClientToolCode(hardID)            #使用硬件码+特殊字符串对试用代码进行AES加密
        outstr = json.dumps(backdic)
        self.sendMsg(outstr)

    def hardLogin(self,hardMsgObj):
        isReg = False
        hardID = hardMsgObj['HardID']
        regIDCOde = ''
        hardobj = hardKeysToolObj.getHardMsg(hardID)
        if hardobj != None:
            if len(hardobj['regID']) <5:
                hardMsgObj['regID'] = ''
                hardKeysToolObj.addHardMsgToDB(hardMsgObj)
            else:
                regid = hardobj['regID']
                hardtmp = regKeysToolObj.getRegCodeData(regid)
                if hardtmp != None and hardtmp['hard']['HardID'] == hardobj['HardID']:
                    #软件已注册过
                    isReg = True
                    regIDCOde = regid
                else:
                    hardMsgObj['regID'] = ''
                    hardKeysToolObj.addHardMsgToDB(hardMsgObj)
        else:
            hardKeysToolObj.addHardMsgToDB(hardMsgObj)
        if isReg:
            if 'getCode' in hardMsgObj: #是否请求加密代码
                backdic = {}
                backdic['erro'] = 0
                backdic['regID'] = regIDCOde
                backdic['code'] = getADSCodeRegUser(hardID,regIDCOde)    #使用注册码+硬件码+特殊字符串对代码进行AES加密
                backdic['msg'] = ''#isOK
                outstr = json.dumps(backdic)
                self.sendMsg(outstr)
            else:
                backdic = {}
                backdic['erro'] = 0
                backdic['code'] = ''    #使用注册码+硬件码+特殊字符串对代码进行AES加密
                backdic['msg'] = ''
                outstr = json.dumps(backdic)
                self.sendMsg(outstr)
        else:
            if 'getCode' in hardMsgObj: #是否请求加密代码
                backdic = {}
                backdic['erro'] = 1
                backdic['code'] = getAESCodeTrail(hardID)  #使用硬件码+特殊字符串对试用代码进行AES加密
                backdic['msg'] = '软件未注册可试用%d次'%(UserDBTool.MAXTESTCOUNT)
                outstr = json.dumps(backdic)
                self.sendMsg(outstr)
            else:
                backdic = {}
                backdic['erro'] = 1
                backdic['code'] = ''            #使用硬件码+特殊字符串对试用代码进行AES加密
                backdic['msg'] = '软件未注册可试用%d次'%(UserDBTool.MAXTESTCOUNT)
                outstr = json.dumps(backdic)
                self.sendMsg(outstr)
        self.saveClientIP(hardID)#保存用户登陆IP地址
            
    def registClient(self,hardMsgObj):
        regID = hardMsgObj['regID']
        hardID = hardMsgObj['HardID']
        isOK = regKeysToolObj.addHardMsgToRegDB(regID, hardMsgObj)
        if isOK:
            backdic = {}
            backdic['erro'] = 0
            backdic['code'] = getADSCodeRegUser(hardID,regID)    ##使用注册码+硬件码+特殊字符串对代码进行AES加密
            backdic['msg'] = '软件注册成功，谢谢使用，如有问题可联系QQ:1983246448'
            outstr = json.dumps(backdic)
            hardKeysToolObj.setResCodeWithHardMsg(hardMsgObj, regID)
            self.sendMsg(outstr)   #注册成功，发送密码和加密后的代码
        else:
            backdic = {}
            backdic['erro'] = 1
            backdic['reskey'] = ''
            backdic['code'] = ''
            backdic['msg'] = '注册码无效，请核对是否输入正确'
            outstr = json.dumps(backdic)
            self.sendMsg(outstr)                   #发送注册失败消息

    def checkClient(self,hardMsgObj):
        regID = hardMsgObj['regID']
        hardID = hardMsgObj['HardID']
        hardtmp = regKeysToolObj.getRegCodeData(regID)
        # print(hardtmp)
        # print(type(hardtmp))
        # print(type(hardtmp['hard']))
        if hardtmp != None and hardtmp['hard']['HardID'] == hardID:
            #软件已注册过
            if 'getCode' in hardMsgObj:   #是否请求加密代码
                backdic = {}
                backdic['erro'] = 0
                backdic['code'] = getADSCodeRegUser(hardID,regID)  #使用注册码+硬件码+特殊字符串对代码进行AES加密
                backdic['msg'] = ''#isCheckOK
                outstr = json.dumps(backdic)
                self.sendMsg(outstr) 
            else:
                backdic = {}
                backdic['erro'] = 0
                backdic['reskey'] = ''
                backdic['code'] = ''
                backdic['msg'] = ''#isCheckOK
                outstr = json.dumps(backdic)
                self.sendMsg(outstr)
        elif hardMsgObj['regID'] != '':
            hardMsgObj['regID'] = ''
            hardKeysToolObj.addHardMsgToDB(hardMsgObj)
            if 'getCode' in hardMsgObj:   #是否请求加密代码
                backdic = {}
                backdic['erro'] = 1
                backdic['code'] = getAESCodeTrail(hardID)    #使用硬件码+特殊字符串对试用代码进行AES加密
                backdic['msg'] = '软件未注册可试用%d次'%(UserDBTool.MAXTESTCOUNT)
                outstr = json.dumps(backdic)
                self.sendMsg(outstr) 
            else:
                backdic = {}
                backdic['erro'] = 1
                backdic['code'] = ''                #使用硬件码+特殊字符串对试用代码进行AES加密
                backdic['msg'] = '软件未注册可试用%d次'%(UserDBTool.MAXTESTCOUNT)
                outstr = json.dumps(backdic)
                self.sendMsg(outstr)
        else:
            self.sendEmptyMsg()

    def saveDownloadURL(self,msgObj):
        hardID = msgObj['HardID']
        purl = msgObj['url']
        if type(purl) == list:
            count = userdbtoolobj.addUserListDBWithRegCode(hardID, purl)
        else:
            count = userdbtoolobj.addUserDBWithRegCode(hardID, purl)
        if msgObj['isTrail'] == 1 and count > UserDBTool.MAXTESTCOUNT: #加上这个可以减少服务器读取数据库的操作
            backdic = {}
            backdic['erro'] = 1
            backdic['count'] = count            #使用硬件码+特殊字符串对试用代码进行AES加密
            backdic['msg'] = '软件未注册可试用%d次'%(UserDBTool.MAXTESTCOUNT)
            outstr = json.dumps(backdic)
            self.sendMsg(outstr)
        else:
            regCode = hardKeysToolObj.getHardHeaveResCode(hardID)
            if regCode == None or (len(regCode) < 5 and count > UserDBTool.MAXTESTCOUNT):
                backdic = {}
                backdic['erro'] = 2
                backdic['count'] = count            #使用硬件码+特殊字符串对试用代码进行AES加密
                backdic['msg'] = '软件未注册可试用%d次'%(UserDBTool.MAXTESTCOUNT)
                outstr = json.dumps(backdic)
                self.sendMsg(outstr)
            else:
                backdic = {}
                backdic['erro'] = 0
                backdic['count'] = count
                backdic['msg'] = ''
                outstr = json.dumps(backdic)
                self.sendMsg(outstr)

    
    def cleintPublicKey(self,publickey):
        pass

    def creageRegIDs(self,pCount = 50):
        keys,isOK = regKeysToolObj.createRegistCode(pCount)
        if isOK:
            outs = json.dumps(keys)
            print outs
            self.sendMsg(outs)
        else:
            return None

    def createRegIDSFro1Ka(self,pCount = 50):
        keys,isOK = regKeysToolObj.createRegistCode(pCount)
        if isOK:
            outs = ''
            for i in range(len(keys)):
                outs += keys[i] + ','
            outs = outs[:-1]
            self.sendMsg(outs,isCompress = False)
        else:
            self.sendEmptyMsg()

    def saveClientIP(self,hardID):
        userdbtoolobj.addUserDBIPWithHardID(hardID,self.client_address[0])

    def do_GET(self):  
    	print('clientIP-->',self.client_address[0])
        print('clienturl-->',self.path)

        if self.path=="/":  
            self.path="/index.html"  
        try:  
            #根据请求的文件扩展名，设置正确的mime类型  
            if self.path.endswith(".html"):  
                mimetype='text/html'  
                f = open(curdir + os.sep + self.path, 'rb')  
                self.send_response(200)  
                self.send_header('Content-type',mimetype)  
                self.end_headers()  

                self.wfile.write(f.read())  
                f.close()  
                return
            elif self.path.endswith(".png"):
                mimetype = 'image/png'
                f = open('./store/image.png', 'rb')  
                self.send_response(200)  
                self.send_header('Content-type',mimetype)  
                self.end_headers()  
                self.wfile.write(f.read())  
                f.close()  
                return 
            #客户端请求服务器公钥
            elif self.path.endswith(".pem"):
                mimetype = 'application/text'
                f = open(curdir + os.sep + self.path, 'rb')  
                self.send_response(200)  
                self.send_header('Content-type',mimetype)  
                self.end_headers()  
                self.wfile.write(f.read())  
                f.close()  
                return 
            elif self.path.endswith(".json"): #更新的update.json文件获取
                mimetype = 'application/json'
                f = open(curdir + os.sep + self.path, 'rb')  
                self.send_response(200)  
                self.send_header('Content-type',mimetype)  
                self.end_headers()  
                self.wfile.write(f.read())  
                f.close()  
                return 
            
            if self.client_address[0] == '':
                print self.client_address[0]

            if self.path[1:6] == 'trail':    #1.client试用登陆
                print('trail---->',self.path)
                return 'trail'
            elif self.path[1:5] == 'code':
                return 'code'
            elif self.path[1:5] == 'bind':   #2.client绑定注册码和硬件码
                print('bind---->',self.path)
                return 'bind'
            elif self.path[1:6] == 'check':  #3.client验证注册码和硬件码
                print('check---->',self.path)
                return 'check'
            elif self.path[1:4] == 'msg':   #有户提交下载数据
                print('msg-->',self.path)
                
                return 'msg'

            elif self.path[1:11] == 'userPubkey':#客户端发送RSA公钥上来
                print('userPubkey--->',self.path)
                return 'userPubkey'
            elif self.path[1:7] == 'create': #1.易卡生成注册码
                #https://www.xxxx.com/create?type=1
                #https://www.xxxx.com/create?type=1&count=50
                #返回:卡 密,卡 密,卡 密
                #只有卡时返回:卡,卡,卡,卡
                print('create-->',self.path)
                return 'create'
            elif self.path[1:7] == 'selled': #2.1k出售成功
                #异步通知地址:www.xxxx.com/selled
                #POST一共会传递4个参数goods_id,trade_no,card_password,contact
                #goods_id : 商品ID
                #trade_no : 订单ID
                #card_password : 卡密,多个卡密之间用|分割,卡和密用逗号,分割
                #contact : 联系方式
                print('selled---->',self.path)
                return 'selled'
            elif self.path[1:9] == 'mycreate':  #1.手动创建新的卡密
                return 'mycreate'
            else:
                time.sleep(3)
                self.sendEmptyMsg()
            return  
  
        except IOError:  
            self.send_error(404,'File Not Found: %s' % self.path)  
  
    def do_POST(self):

        reqtype = self.do_GET()
        # try:
        if True:
            length = self.headers.getheader('content-length');
            nbytes = int(length)
            data = self.rfile.read(nbytes)

            data = self._decompress(data)
                
            print('postGetData---->',len(data))
            msgobj = json.loads(data)
            # print(msgobj)
            if reqtype == 'trail':  #硬件登陆
                # print('硬件登陆:\n硬件码:%s'%(msgobj['HardID']))
                self.hardLogin(msgobj)

            elif reqtype == 'bind': #用户输入注册码
                # print(msgobj['HardID'],msgobj['regID'])
                # print('绑定注册码:\n硬件码:%s\n注册码:%s'%(msgobj['HardID'],msgobj['regID']))
                self.registClient(msgobj)
            elif reqtype == 'check':
                # print('客户端校验身份:\n硬件码:%s\n注册码:%s'%(msgobj['HardID'],msgobj['regID']))
                self.checkClient(msgobj)
            elif reqtype == 'msg':
                # print('客户端提交下载地址:\n硬件码:%s\n下载地址:%s'%(msgobj['HardID'],msgobj['url']))
                self.saveDownloadURL(msgobj)
            elif reqtype == 'userPubkey': 
                # print('客户端发送自已公钥上来')
                pass

            elif reqtype == 'create':
                # print('易卡请求生成注册码')
                # self.createRegIDSFro1Ka()
                pass
            elif reqtype == 'selled':
                # print('易卡有卡密已出售')
                pass

            elif reqtype == 'code':
                # print('获取客户端程序')
                self.sendClientRegToolCode(msgobj)
            elif reqtype == 'mycreate':
                # print('手动请求生成卡密')
                if msgobj['key'] == createKey:
                    self.creageRegIDs(msgobj['count'])
                else:
                    time.sleep(5)
                    self.sendEmptyMsg()
        # except Exception as e:
            # self.send_error(404,'File Not Found: %s' % self.path)  
    def sendEmptyMsg(self):
        self.send_response(200)
        self.send_header("Content-type", 'application/xml; encoding=utf-8')
        self.send_header("Content-Length", str(''))
        self.end_headers()
        self.wfile.write('')

    def sendMsg(self,msg,isCompress = True):
        outstr = ''
        if isCompress:
            demsg = self._compress(msg)
            outstr = base64.b64encode(demsg)
        else:
            outstr = msg
        self.send_response(200)
        self.send_header("Content-type", 'application/text; encoding=utf-8')
        self.send_header("Content-Length", str(len(outstr)))
        self.end_headers()
        self.wfile.write(outstr)

    #校验消息真实性
    def verifyMsg(self,reqdict):
        tokenver = []
        tokenver.append('tokenxxx')
        tokenver.append(reqdict['nonce'])
        tokenver.append(reqdict['timestamp'])
        tokenver.sort()
        tmpstr = tokenver[0] + tokenver[1] + tokenver[2]
        sha1str = hashlib.sha1(tmpstr).hexdigest()
        if sha1str == reqdict['signature']:
            return True
        else:
            return False

    def _compress(self,msg):
        dat = zlib.compress(msg, zlib.Z_BEST_COMPRESSION)
        # print('ziplen-co-->',len(msg),len(dat))
        return dat
    def _decompress(self,dat):
        msg = zlib.decompress(dat)
        # print('ziplen-de-->',len(dat),len(msg))
        return msg


    def do_HEAD(self):
        """Serve a HEAD request."""
        print('do_HEAD')
        f = self.send_head()
        if f:
            f.close()

    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        f = StringIO()
        displaypath = cgi.escape(urllib.unquote(self.path))
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>Directory listing for %s</title>\n" % displaypath)
        f.write("<body>\n<h2>Directory listing for %s</h2>\n" % displaypath)
        f.write('''<form action="" enctype="multipart/form-data" method="post">\n
                    <input name="file" type="file" />
                    <input value="upload" type="submit" />
                </form>''')
        f.write("<hr>\n<ul>\n")
        for name in list:
            if name.startswith('.'):
                continue
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            f.write('<li><a href="%s">%s</a>\n'
                    % (urllib.quote(linkname), cgi.escape(displayname)))
        f.write("</ul>\n<hr>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        encoding = sys.getfilesystemencoding()
        self.send_header("Content-type", "text/html; charset=%s" % encoding)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = os.getcwd()
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path

    def copyfile(self, source, outputfile):
        """Copy all data between two file objects.

        The SOURCE argument is a file object open for reading
        (or anything with a read() method) and the DESTINATION
        argument is a file object open for writing (or
        anything with a write() method).

        The only reason for overriding this would be to change
        the block size or perhaps to replace newlines by CRLF
        -- note however that this the default server uses this
        to copy binary data as well.

        """
        shutil.copyfileobj(source, outputfile)

    def log_error(self, format, *args):
        """Log an error.

        Display error message in red color.
        """

        format = '\033[0;31m' + format + '\033[0m'
        self.log_message(format, *args)

    def guess_type(self, path):
        """Guess the type of a file.

        Argument is a PATH (a filename).

        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.

        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.

        """
        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


f = open('./keys/server.conf','r')
lines = f.readlines()
f.close()
tmpIp = lines[0].replace('\n','').replace('\r','')
tmpPort = int(lines[1].replace('\n','').replace('\r',''))

serverAddr = (selfip,tmpPort)

if selfip[0:2] != '19':
    serverAddr = (tmpIp,tmpPort)

def runHttpServer(ptemp):

    server = ThreadedHTTPServer(serverAddr, myHandler)
    print('https server is running....')
    print('Starting server, use <Ctrl-C> to stop')
    print(serverAddr)
    
    server.socket = ssl.wrap_socket (server.socket, certfile='./keys/server.pem', server_side=True)
    server.serve_forever()
def startServer():

    thr = threading.Thread(target=runHttpServer,args=(None,))
    thr.setDaemon(True)
    thr.start()


if __name__ == '__main__':
    # server = ThreadedHTTPServer(serverAddr, myHandler)
    # print 'https server is running....'
    # print 'Starting server, use <Ctrl-C> to stop'
    # server.socket = ssl.wrap_socket (server.socket, certfile='server.pem', server_side=True)
    # server.serve_forever()
    startServer()
    while True:
        time.sleep(10)


# # 生成rsa密钥
# $ openssl genrsa -des3 -out server.key 2048
# # 去除掉密钥文件保护密码
# $ openssl rsa -in server.key -out server.key
# # 生成ca对应的csr文件
# $ openssl req -new -key server.key -out server.csr
# # 自签名
# $ openssl x509 -req -days 2048 -in server.csr -signkey server.key -out server.crt
# $ cat server.crt server.key > server.pem
