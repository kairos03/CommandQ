import unittest
import multiprocessing as mp
import time
import logging

import server


class ServerTest(unittest.TestCase):
    def test_scheduler(self):
        running = mp.Queue(1)
        readyq = mp.Queue()
        signal = mp.Queue()

        serv = mp.Process(target=server.scheduler, args=(running, readyq, signal))
        serv.start()
        time.sleep(1)

        signal.put('kill')
        time.sleep(3)

        readyq.put(['sleep', '2'])
        readyq.put(['echo', '1'])
        readyq.put(['echo', '2'])
        readyq.put(['echo', '3'])
        time.sleep(10)

        readyq.put(['sleep', '10'])
        time.sleep(1)
        signal.put('kill')
        time.sleep(5)

        serv.kill()