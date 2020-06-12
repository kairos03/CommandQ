import fcntl
import os
from subprocess import Popen, PIPE, STDOUT
import logging


class LoggingProcess:
    def __init__(self, args):
        self.args = args
        self.start()

    def _getOutput(self): #non blocking read of stdout
        try:
            return self.process.stdout.readline()
        except:
            pass

    def start(self):
        self.process = Popen(args=self.args, bufsize=1, stdout=PIPE, stderr=STDOUT) #line buffered
        # make process stdout non-blocking
        fd = self.process.stdout
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def poll(self):
        return self.process.poll()

    def kill(self):
        return self.process.kill()

    def writeLog(self):
        line = self._getOutput()
        if line:
            logging.info(line.strip()) 