import argparse
import subprocess
import time
from multiprocessing import Process, Queue, Manager
from multiprocessing.connection import Listener
import traceback
import logging


address = ('localhost', 6000)


def show_queue(queue):
    q = []
    for _ in range(queue.qsize()):
        item = queue.get()
        queue.put(item)
        q.append(item)
    return q


def del_queue(queue, index):
    for i in range(queue.qsize()):
        item = queue.get()
        if i != index:
            queue.put(item)


def server(running, readyq, signal):
    # server listener
    with Listener(address, authkey=b'secret password') as listener:
        while True:
            try:
                # business flow 
                with listener.accept() as conn:
                    logging.info(f'connection accepted from: {listener.last_accepted}')
                    
                    # get command and args
                    req = conn.recv()
                    cmd = req['cmd']
                    args = req['args']
                    
                    # stop
                    if req['cmd'] == 'stop':
                        conn.send("Server Stopped.")
                        exit(0)
                    
                    # ls
                    elif cmd == 'ls':
                        run = show_queue(running)[0]
                        ready = show_queue(readyq)

                        print('curq: ', run)
                        print('readyq', readyq)

                        status = 'Running' if run[1] == None else 'Finish' if run[1] >= 0 else 'Killed'
                        res = f'[0] {" ".join(run[0])} | {status}\n'
                        for i, job in enumerate(reversed(ready)):
                            res += f'[{i+1}] {" ".join(job)}\n'
                        conn.send(res)
                    
                    # add
                    elif cmd == 'add':
                        readyq.put(args)
                        conn.send(f'Job Added to {readyq.qsize()}.')
                    
                    # del
                    elif req['cmd'] == 'del':
                        no = args
                        if no == 0:
                            signal.put('kill')
                        else:
                            del_queue(readyq, no)
                            conn.send(f'Job [{no}] deleted.')                
            except Exception:
                traceback.print_exc()


def scheduler(running, readyq, signal):
    try:
        process = subprocess.Popen(args=['echo'])
        running.put((['Empty'], 0))
        
        while True:
            logging.debug("===================")
            logging.debug(f'runner: {process} {process.poll()}')
            logging.debug(f'{show_queue(readyq)} {show_queue(signal)}')
            logging.debug("===================")
            
            if process.poll() == None and not signal.empty():
                if signal.get() == 'kill':
                    process.kill()
                    logging.info('killed')

            if process.poll() != None:
                logging.info('wait')
                cmd = readyq.get()
                logging.info('run')
                process = subprocess.Popen(args=cmd)
            
            # update running process status
            ## may cause sync error
            running.get()
            running.put((process.args, process.poll()))
    finally:
        process.kill()


if __name__ == '__main__':
    try:
        running = Queue(1)
        readyq = Queue()
        signal = Queue()
        print('Server Started.')
        serv = Process(target=scheduler, args=(running, readyq, signal), daemon=True)
        serv.start()
        server(running, readyq, signal)
        serv.join()
    finally:
        print('Server Stopped.')
        serv.kill()
        