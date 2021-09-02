# from eventlet import monkey_patch; monkey_patch() # can't work
from options.process_config import Options
from process.process import SubProcess
from utils import Unbuffered
import select
import time
import os
import sys
pro_list = []
options = []
options.append(Options(cmd=("ping 127.0.0.1"), delay=0, log_file=None, name="ping"))
options.append(Options(cmd=("python -u python_cmd_sample.py"), delay=0, log_file=None, name="python"))



proc_map = {}

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
    print("process id is %d" % pid)
    proc_map[stdout_fd] = proc



while True:
    r_fds, w_fds, x_fds = select.select(proc_map.keys(), [], [], 2)
    if not r_fds:
        continue
    print("********%s********" % " ".join(map(str, r_fds)))
    for fd in r_fds:
        proc = proc_map.get(fd, None)
        print("fd:%s, name: %s" % (fd, proc.options.name)) # 当python进程报错或者结束时,event就是一直是16
        

        output = proc.drain_stdout()
        if output:

            print(output, end="")
            # TODO emit all connector
        else: #建立在一个假设上: fd对应的event是16时,意味着进程结束(有一个显而易见的bug是,如果cmd出于什么原因主动关闭了对应的fd的写入端,那么进程不应该结束)
            if proc.poll() is None:
                print("proc: %s actively closed fd: %d" % (proc.options.name, fd))
            else:
                proc.init_status() # release fds when process is over
            print("process: %s  status --> %s" % (proc.options.name, proc.status))
            del proc_map[fd]
            # release process pid
            os.waitpid(-1, os.WNOHANG)



# else:
#     sock_conn = socket_map[fd]
#     if sock_conn == http_server.server_socket:
#         new_conn, addr = http_server.accept()
#         print("%s:%s connected" % addr)
#         socket_map[new_conn.fileno()] = new_conn
#     elif event & select.EPOLLHUP:
#         epoll.unregister(fd)
#         sock_conn.close()
#         del socket_map[fd]
#     elif event & select.EPOLLIN:
#         data = http_server.read(sock_conn)
                
    
    # TODO deal socket event

