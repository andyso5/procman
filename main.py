#-*- coding: utf-8 -*-

"""
1. 使用epoll模型去监听进程输出流事件与运行状态
2. 用epoll模型去监听web端事件
3. 使用websocket协议实时上传进程输出流与运行状态

# TODO python3中, 协程的本质也是用epoll来实现的, 所以没必要强行引入epoll

# TODO websocket/socketio 的协议太复杂,最好退而求其次, 通过管道或者什么的将收集到的信息通过flask传递给前端
# TODO 那么这样一来, 也就没必要自己建一个http server了
# TODO 纯使用epoll模型,不太好实现延迟,必须引入协程或者进/线程
# TODO 最好能使用管道与flask通信, 这也意味使用进程来启动核心
# TODO 弄一个进程专门来计时,秒级计时
"""


"""
需求:
    第一阶段:
    √   1. 根据option的自启选项,在程序启动时,自动启动节点        
        2. 若需要自启的节点有延时请求, 需要延时
    √   3. 节点退出需要能检测得到, 并且可以知道是否因异常而退出    
    √   4. 实时输出各个节点的输出流与异常流                     
        5. 节点退出自动在一段时间后自动重启一定次数
    第二阶段: 
        1. 接受启动命令,并且在检查到节点在停止状态后启动
        2. 接受查询命令, 返回该节点的当前状态
        3. 接受停止命令, 检查到节点在非停止状态后,停止节点, 若节点在一定时间内未能停止,则杀死节点进程
    第三阶段:
        1. 使用flask开发http后端, 使用http请求来启动, 查询和停止节点
        2. 使用websocket实时发送节点的输出流与节点状态

"""
from eventlet import monkey_patch; monkey_patch() # 使用monkey_path后select就没有poll与epoll了
from options.process_config import Options
from process.process import SubProcess
import time
import os
import sys
import select



pro_list = []
options = []
proc_map = {}

options.append(Options(cmd=("ping 127.0.0.1"), delay=0, log_file=None, name="ping"))
options.append(Options(cmd=("python -u python_cmd_sample.py"), delay=0, log_file=None, name="python"))

for option in options:
    proc = SubProcess(option)
    pro_list.append(proc)



for proc in pro_list:
    proc.spawn()
    pid = proc.pid
    stdout_fd = proc.stdout_fd
    print("process id is %d" % pid)
    proc_map[stdout_fd] = proc

r, w = os.pipe()
print("$$$%s" % proc.poll())
epoll = select.poll()
for pro in pro_list:
    epoll.register(pro.stdout_fd, select.EPOLLIN)

