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

cd market/bitmex_xbt

sh startDataServer.sh

sh startTradeServer.sh

sleep 5

sh runWatchdog.sh

cd $basepath

cd market/okex

sh startDataServer.sh

sh startTradeServer.sh

sleep 5

sh runWatchdog.sh


cd $basepath

LOG=`nohup python3 mainClient.py > mlog.txt 2>&1 & echo $!`
# LOG="12345"
echo $LOG
OUTSTR=$DATE"\n"$LOG
echo $OUTSTR > mpsid.txt

# #打开bitmex合约工具
# osascript -e 'tell app "Terminal"
#     do script "cd ~/Documents/github/okex_robot/market/bitmex;sh startDataServer.sh"
# end tell'


# sleep 1

# osascript -e 'tell app "Terminal"
#     do script "cd ~/Documents/github/okex_robot/market/bitmex;sh startTradeServer.sh"
# end tell'


# sleep 1


# # 打开okex季度合约工具
# osascript -e 'tell app "Terminal"
#     do script "cd ~/Documents/github/okex_robot/market/okex;sh startDataServer.sh"
# end tell'

# sleep 1

# osascript -e 'tell app "Terminal"
#     do script "cd ~/Documents/github/okex_robot/market/okex;sh startTradeServer.sh"
# end tell'

# sleep 5

#启动管理客户端
# python mainClient.py