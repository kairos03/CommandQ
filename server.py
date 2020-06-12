import argparse
import subprocess
import time
from multiprocessing import Process, Queue, Manager
from multiprocessing.connection import Listener
import traceback
import logging


from LoggingProcess import LoggingProcess


def get_args():
    parser = argparse.ArgumentParser('Command Queue Server')
    parser.add_argument('ip', help='Server IP')
    parser.add_argument('port', help='Server port')
    parser.add_argument('--log_file', default='cq.log', help='logging file')
    return parser.parse_args()


def server(address, ns):
    # server listener
    with Listener(address, authkey=b'secret password') as listener:
        logging.info('Server Initialized')
        while True:
            try:
                # business flow 
                with listener.accept() as conn:
                    logging.debug(f'Connection accepted from: {listener.last_accepted}')
                    
                    # get command and args
                    req = conn.recv()
                    cmd = req['cmd']
                    args = req['args']
                    logging.debug(f'Command recive: {cmd} {args} from {listener.last_accepted}')

                    # stop
                    if req['cmd'] == 'stop':
                        conn.send("Server Stopped.")
                        exit(0)
                    
                    # ls
                    elif cmd == 'ls':
                        status = 'Running' if ns.running[1] == None else 'Finish' if ns.running[1] >= 0 else 'Terminated'
                        res = f'[0] {" ".join(ns.running[0])} | {status}\n'
                        for i, job in enumerate(reversed(ns.readyq)):
                            res += f'[{i+1}] {" ".join(job)}\n'
                        conn.send(res)
                    
                    # add
                    elif cmd == 'add':
                        ns.readyq.insert(0, args)
                        conn.send(f'Job Added to {len(ns.readyq)}.')
                    
                    # del
                    elif req['cmd'] == 'del':
                        no = args
                        if no == 0:
                            ns.signal='kill'
                            conn.send(f'Running Job [0] killed.')
                        elif no < len(ns.readyq):
                            ns.readyq.pop(len(ns.readyq) - no)
                            conn.send(f'Job [{no}] deleted.')
                        else:
                            conn.send('No such No of job.')
            except Exception:
                traceback.print_exc()


def scheduler(ns):
    try:
        process = LoggingProcess(['echo'])
        ns.running = (['Empty'], 0)
        logging.info('Scheduler initialized')
        
        while True:
            if process.poll() == None and ns.signal == 'kill':
                process.kill()
                ns.signal = None
                logging.info('Running Process killed')

            if process.poll() != None and len(ns.readyq) > 0:
                cmd = ns.readyq.pop()
                logging.info(f'Run New Command: {cmd}')
                process = LoggingProcess(cmd)
            
            # update running process status
            process.writeLog()
            ns.running = (process.args, process.poll())
    finally:
        process.kill()


if __name__ == '__main__':
    args = get_args()
    address = (args.ip, int(args.port))
    logging.basicConfig(filename=args.log_file,
                        format='%(asctime)s %(name)s:%(levelname)s:%(message)s',
                        level=logging.INFO)

    try:
        manager = Manager()
        ns = manager.Namespace()
        ns.running = None
        ns.readyq = manager.list()
        ns.signal = None

        logging.info('Server Started')
        serv = Process(target=scheduler, args=(ns,), daemon=True)
        serv.start()
        server(address, ns)
        serv.join()
    finally:
        logging.info('Server Stopped')
        serv.kill()
        