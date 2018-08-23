#!bin/bash
#create buy zhangjunpeng @ 2016
#export PATH=/Users/junpengzhang/Documents/android/apktool:
#安卓sdk
#export PATH=/Users/junpengzhang/Documents/android/android_sdk/build-tools/25.0.0:
export PATH=/usr/bin/:/usr/local/bin:/bin:

CUR_PATH=`pwd`
basepath=$(cd `dirname $0`; pwd)
echo $basepath
echo $CUR_PATH

#获取当前目录的命令是pwd
#获取脚本所在目录是${cd `dirname `; pwd},把{换成括号，模版里不识别括号
#运行程序，并保存pid
#获取日期和时间
#DATE=`date "+%Y-%m-%d-%H:%M:%S"`
DATE=`date "+%Y-%m-%d %H:%M:%S"`
echo $DATE

cd $basepath
python3 okexTradeServer.py
