#!/usr/bin/python
# -*- coding: utf-8 -*-
#用于访问OKCOIN 期货REST API

import websocket
import socket
import sys

try:
    import thread
except ImportError:
    import _thread as thread
import time
import json

class WsTool(object):
    """docstring for WsTool"""
    def __init__(self, arg):
        super(WsTool, self).__init__()
        self.arg = arg
    def on_message(ws, message):
        print('-----getMsg------')
        print(message)
        print(type(message))
        # msg = str(message)
        # dtool.onMessage(message)

    def on_error(ws, error):
        print('-----eoor------')
        print(error)

    def on_close(ws):
        print("### closed ###")

    def on_open(ws):
        print('is Open')
        # def run(*args):
        #     # for i in range(3):
        #     #     time.sleep(1)
        #     #     ws.send("Hello %d" % i)
        #     # time.sleep(1)
        #     # ws.close()
        #     # print("thread terminating...")
        #     # msg = {"op": "subscribe", "args": ["tradeBin1m:XBTUSD","orderBook10:XBTUSD"]}
        #     # msg = {"op": "subscribe", "args": ["tradeBin1m:XBTUSD","orderBookL2:XBTUSD"]}
        #     msg = {"op": "subscribe", "args": ["tradeBin1m:XBTUSD"]}
        #     # msg = {"op": "subscribe", "args": ["quoteBin1m:XBTUSD"]}#instrument
        #     # msg = {"op": "subscribe", "args": ["instrument:XBTUSD"]}#instrument
        #     # msg = "help"
        #     jstr = json.dumps(msg)
        #     ws.send(jstr)
        # thread.start_new_thread(run, ())

def test():
    # import datetime

    # dat = datetime.datetime(2000,1,1,8,0)
    # print(dat)
    for i in [12.12300, 12.00, 200.12000, 200.0]:
        d = '{:g}'.format(i)
        print(type(d))
        print(float(d))
        print('{:g}'.format(i))


def main():
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://real.okex.com:10440/websocket/okexapi",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()

if __name__ == "__main__":
    test()

    
