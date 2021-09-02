import os
import fcntl
import subprocess
from types import MethodType
import process.constants as cons



def switch(func):
    """Aviod always checking whether this process has stepped into work status"""
    def _wrapper(self, *args, **kwargs):
        ret = func(self, *args, **kwargs)
        if self.status & cons.PROC_WORKING:
            print("check ")
            self.drain_stdout = MethodType(self.__class__.drain_stdout_without_check, self)
        return ret

    return _wrapper

class SubProcess(object):
    def __init__(self, options):
        self.options = options
        self.pid = None
        self.proc_handle = None
        self.stdin_handle = None
        self.stdout_handle = None
        self.stdin_fd = None 
        self.stdout_fd = None
        self.status = cons.PROC_INIT # TODO realize the six status
        
    def set_noblock(self, fd):
        # TODO why ?
        fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)

    def spawn(self, pre_exec=None):
        # write_end: end of pipe to write
        # read_end:  end of pipe to read
        self.status = cons.PROC_STARTING
        if pre_exec is None:
            pre_exec = self.pre_exec
            
        stdin_read_end, stdin_write_end = os.pipe()
        stdout_read_end, stdout_write_end = os.pipe()
        
        # TODO Figure out it's value
        # It is copied from Supervisor
        for fd in (stdin_write_end, stdout_read_end):
            flags = fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NDELAY
            fcntl.fcntl(fd, fcntl.F_SETFL, flags)

        proc = subprocess.Popen(
            args=self.options.cmd,
            stdin=stdin_read_end,
            stdout=stdout_write_end,
            stderr=stdout_write_end,
            bufsize=1,              # line buffer mode
            preexec_fn = pre_exec,
            universal_newlines=True # '\r\n' and '\r' are seen as '\n'
            )

        # close it to release fds in main process
        # avoid using too many fds when frequently start and stop processes
        os.close(stdout_write_end)
        os.close(stdin_read_end)

        self.pid = proc.pid

        self.status = cons.PROC_INIT


        self.stdin_fd = stdin_write_end 
        self.stdout_fd = stdout_read_end

        self.set_noblock(stdout_read_end)

        self.stdin_handle = os.fdopen(stdin_write_end, "w", 1)
        self.stdout_handle = os.fdopen(stdout_read_end, "r", 1)
        self.proc_handle = proc

    def checked_work_signal(self):
        # TODO
        self.status = cons.PROC_WORKING
    
    #@switch
    def drain_stdout(self):
        """Try always read string in stdout_fd
        """
        # read and readlines may continue until EOF
        # but fd is not end

        #return "".join(self.stdout_handle.readlines()) #it will block
        #return self.stdout_handle.readline(-1) # as same as not argument
        #return self.stdout_handle.read() # it will block
        #return os.read(self.stdout_fd, 1024).decode() # work
        #return self.stdout_handle.recv(1024) # Socket operation on non-socket, failed


        """If the process is over, os.read will block, still"""
        # TODO checked the signal representing subprocess is working

        return self.stdout_handle.read()

    def drain_stdout_without_check(self):
        return self.stdout_handle.read()


    def terminate(self, check_poll=False):
        """
        Terminate process 
        """
        if check_poll:
            self.poll()
        if self.status & cons.PROC_INIT | self.status & cons.PROC_WORKING:
            self.proc_handle.terminate()
            self.status = cons.PROC_STARTING
            # TODO use join or os.waitpid to change status into PROC_STOP

        # Seems the stdout_fd will be closed automatically after process is over
        else:
            self.init_status()


    def init_status(self):
        fd_dict = {"stdout_fd": self.stdout_fd, "stdin_fd": self.stdin_fd}
        for fd_name, fd in fd_dict.items():
            try:
                os.close(fd)
            except OSError:
                print("%s's %s: %d has been already closed" % (self.options.name, fd_name, self.stdout_fd))
            except Exception as err:
                print("when closing %s's %s: %d, %s  ocurrs" % (self.options.name, fd_name, self.stdout_fd, str(err)))

        status = self.status
        self.__init__(self.options)
        self.status = status
        # recover drain_stdout method as origin
        # TODO monitor working signal from process
        # self.drain_stdout = MethodType(self.__class__.drain_stdout, self) 
    
    def poll(self):
        """
        Check if process is over, and update status.
        """
        # subprocess.Popen::poll returns the value of os._exit(value) in subprocess
        ret = self.proc_handle.poll()
        if ret is None: # If process is running, ret is None
            return ret
        if ret==0:
            self.status = cons.PROC_STOP
        else:
            self.status = cons.PROC_ERROR
        return ret

    def pre_exec(self):
        print("%s starts" % self.options.name)







    



