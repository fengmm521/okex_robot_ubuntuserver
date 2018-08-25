#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-05-24 15:13:31
# @Author  : Your Name (you@example.org)
# @Link    : http://example.org
# @Version : $Id$
#创建SocketServerTCP服务器：
import os,sys
import curses

def main():
    stdscr = curses.initscr()
    pad = curses.newpad(100, 100)
#  These loops fill the pad with letters; this is
# explained in the next section
    for y in range(0, 100):
        for x in range(0, 100):
            try: 
                pad.addch(y,x, ord('a') + (x*x+y*y) % 26 )
            except curses.error: 
                pass

    #  Displays a section of the pad in the middle of the screen
    # pad.refresh( 0,0, 5,5, 20,75)
    pad.refresh()

def test1():
    a= '{"aaaaa"}{"ddddd"}'
    ds = a.split('}{')
    print(ds)

#测试
if __name__ == '__main__':
    test1()
    
    
