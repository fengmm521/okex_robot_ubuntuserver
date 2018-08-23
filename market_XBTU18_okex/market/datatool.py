#!/usr/bin/python
# -*- coding: utf-8 -*-
#用于访问OKCOIN 期货REST API

import os,sys
import json

def getAllData():
    #[1531061101, [[6779.54, 163, 2.4042, 2.4042, 163], [6779.53, 7, 0.1032, 2.5074, 170], [6778.75, 150, 2.2127, 4.7201, 320], [6778.59, 82, 1.2096, 5.9297, 402], [6778.42, 136, 2.0063, 7.936, 538]], [[6782, 54, 0.7962, 0.7962, 54], [6782.92, 150, 2.2114, 3.0076, 204], [6783.18, 150, 2.2113, 5.2189, 354], [6783.44, 150, 2.2112, 7.4301, 504], [6783.63, 150, 2.2112, 9.6413, 654]]]
    fo = open('okex/okexdeep.txt','r')
    lineos = fo.readlines()
    fo.close()

    print('bitmex lines:',len(lineos))
    count = 0
    outokex = []
    oktimes = []
    for l in lineos:
        tmpl = l.replace('\n','')
        d = json.loads(tmpl)
        outokex.append(d)
        oktimes.append(d[0])
        count += 1
        if count %10000 == 0:
            print(count)

    f = open('bitmex/bitmexdeep.txt','r')
    linebs = f.readlines()
    f.close()

    print('bitmex lines:',len(linebs))
    count = 0

    outbitmex = []
    bitmextimes = []
    for l in linebs:
        tmpl = l.replace('\n','')
        d = json.loads(tmpl)
        outbitmex.append(d)
        bitmextimes.append(d[0])
        count += 1
        if count %10000 == 0:
            print(count)

    okheavebitmex = []
    count = 0
    for t in bitmextimes:
        if t in oktimes and (t not in okheavebitmex):
            okheavebitmex.append(t)
        count += 1
        if count %10000 == 0:
            print(count)

    bitmexheaveok = []
    count = 0
    for t in oktimes:
        if t in bitmextimes and (not t in bitmexheaveok):
            bitmexheaveok.append(t)
        count += 1
        if count %10000 == 0:
            print(count)

    print(len(okheavebitmex),len(bitmexheaveok))
    isEqu = False
    if len(okheavebitmex) == len(bitmexheaveok):
        print('===')
        isEqu = True
    if isEqu:
        okdatas = []
        ts = []
        lastdata = []
        for d in outokex:
            if d[0] in okheavebitmex and (d[0] not in ts):
                okdatas.append([d[0],d[1][0],d[2][0]])
                ts.append(d[0])
                if not lastdata:
                    lastdata = [d,list(okdatas[-1])]
        print(lastdata)

        bitmexdatas = []
        ts = []
        for d in outbitmex:
            if d[0] in okheavebitmex and (d[0] not in ts):
                bitmexdatas.append(d)
                ts.append(d[0])
        okdatas.sort(key=lambda x:x[0])
        bitmexdatas.sort(key=lambda x:x[0])
        return okdatas,bitmexdatas
    return [],[]

def getSubData():
    okds,bitds = getAllData()
    print(okds[1000])
    print(bitds[1000])
    outs = []
    for n in range(len(okds)):
        okd = okds[n]
        btd = bitds[n]
        d = [okd[0],okd[1],okd[2],btd[1],btd[2]]
        outs.append(d)
    return outs

def saveSubData(outs):
    outcsvs = []
    lstr = 'time,okbuy,obuycount,oksell,osellcount,bkbuy,bkbuycount,bksell,bksellcount,obuy-bsell,osell-bbuy,bbuy-osell,bsell-obuy\n'
    for d in outs:
        lstr += str(d[0]) + ',%.2f,%d,%.2f,%d'%(d[1][0],d[1][1],d[2][0],d[2][1])  + ',%.2f,%d,%.2f,%d'%(d[3][0],int(d[3][1]/100),d[4][0],int(d[4][1]/100)) + ',%.2f,%.2f'%(d[1][0]-d[4][0],d[2][0]-d[3][0]) + ',%.2f,%.2f'%(d[3][0]-d[2][0],d[4][0]-d[1][0]) + '\n'
    outstr = lstr[:-1]
    f = open('okex-bitmex.csv','w')
    f.write(outstr)
    f.close()
def main():
    outs = getSubData()
    saveSubData(outs)



if __name__ == '__main__':
    main()
