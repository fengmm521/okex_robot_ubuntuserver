#!/usr/bin/python
# -*- coding: utf-8 -*-
#用于访问OKCOIN 期货REST API

import os
import sys
import time

def getDataPID():
    pid = ''
    if os.path.exists('datapsid.txt'):
        f = open('datapsid.txt','r')
        pid = f.readlines()[1].replace('\n','')
        f.close()
    return pid

def main():
    dataPID = getDataPID()
    print('bitmexDataPID=%s'%(dataPID))
    delaytime = 600
    runtime = 0
    count = 0
    while True:
        time.sleep(1)
        count += 1
        if os.path.exists('sokceterro.txt'):
            dataPID = getDataPID()
            if dataPID != '':
                cmd = '/bin/kill %s'%(dataPID)
                print(cmd)
                os.system(cmd)
            time.sleep(0.1)
            if os.path.exists('datapsid.txt'):
                os.remove('datapsid.txt')
            time.sleep(0.3)
            cmd = '/bin/sh startDataServer.sh'
            print('restart Data Server')
            print(cmd)
            os.system(cmd)
            time.sleep(10)
        if count >= delaytime:
            runtime += 1
            print('runing:',runtime)
            count = 0

if __name__ == '__main__':
    main()





    
