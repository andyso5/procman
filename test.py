from options.process_config import Options
from process.process import SubProcess
from utils import Unbuffered
import select
import time
import os
import sys
import socket
pro_list = []
options = []
proc_map = {}

options.append(Options(cmd=("roscore"), delay=0, log_file=None, name="roscore"))
options.append(Options(cmd=("ping 127.0.0.1"), delay=0, log_file=None, name="ping"))
options.append(Options(cmd=("python -u python_cmd_sample.py"), delay=0, log_file=None, name="python"))

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", 7005))
server.listen(5)


for option in options:
    proc = SubProcess(option)
    pro_list.append(proc)

def test_pre_exec():
    #sys.stdout = Unbuffered(sys.stdout) # useless
    #sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 1) # useless
    print("pre exec")

for proc in pro_list:
    proc.spawn(test_pre_exec)
    pid = proc.pid
    stdout_fd = proc.stdout_fd
    print("process: %s id is %d" % (proc.options.name, pid))
    proc_map[stdout_fd] = proc

r, w = os.pipe()
print("$$$%s" % proc.poll())
epoll = select.epoll()
for pro in pro_list:
    epoll.register(pro.stdout_fd, select.EPOLLIN)

server_fd  = server.fileno()
epoll.register(server_fd, select.EPOLLIN)

proc = pro_list[0]
while True:
    events = epoll.poll(2)
    if not events:
        continue
    for fd, event in events:
        if fd == server_fd: # deal http request
            conn, addr = server.accept()
        else:                   # deal with pipe event
            proc = proc_map.get(fd, None)
            print("fd:%s, event: %s, name: %s" % (fd, event, proc.options.name)) # 当python进程报错或者结束时,event就是一直是16
            

            if event & select.EPOLLIN:
                output = proc.drain_stdout()
                print(output, end="")
                # TODO emit it to all connector
            else: #建立在一个假设上: fd对应的event是16时,意味着进程结束(有一个显而易见的bug是,如果cmd出于什么原因主动关闭了对应的fd的写入端,那么进程不应该结束)
                if proc.poll() is None:
                    print("proc: %s actively closed fd: %d" % (proc.options.name, fd))

                proc.init_status() # release fds when process is over
                print("process: %s  status --> %s" % (proc.options.name, proc.status))
                epoll.unregister(fd)
                # release process pid
                os.waitpid(-1, os.WNOHANG)



