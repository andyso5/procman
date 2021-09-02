class Options(object):
    def __init__(self, cmd, delay, log_file, name):
        self.cmd = tuple(cmd.split())
        self.delay = delay
        self.log_file = log_file
        self.name = name