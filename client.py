import argparse
import subprocess
from multiprocessing.connection import Client


def get_args():
    parser = argparse.ArgumentParser('Command Queue')
    sub_parser = parser.add_subparsers(dest='action', required=True, help='Sub-Command help')
    parser.add_argument('--ip', type=str, default='localhost', help="Set Server ip")
    parser.add_argument('--port', type=int, default='2608', help="Set Server port")

    # start
    parser_server = sub_parser.add_parser('server', help='Server command')
    parser_server.add_argument('server_command', choices=['start', 'stop'], help="Set server status")

    # ls
    sub_parser.add_parser('ls', help='Show command queue')

    # add
    parser_add = sub_parser.add_parser('add', help='Add command to queue')
    parser_add.add_argument('command', nargs='*', help='Command to add queue')

    # del
    parser_add = sub_parser.add_parser('del', help='delete or stop command from queue')
    parser_add.add_argument('number', type=int, help='Command number to delete from queue')

    return parser.parse_args()


def send_command(address, cmd, args=[]):
    try:
        with Client(address, authkey=b'secret password') as conn:
            conn.send({'cmd': cmd, 'args': args})
            return conn.recv()
    except ConnectionRefusedError:
        print("Server is not Running.")
        print("Please start server first.")
        print("\ncommand: ")
        print("cq server start")
        print()
        exit(0)


def client(args):
    address = (args.ip, args.port)
    res = ''

    # start
    if args.action == 'server':
        if args.server_command == 'start':
            subprocess.Popen(['python3', 'server.py', args.ip, str(args.port)])
        
        elif args.server_command == 'stop':
            res = send_command(address, 'stop')
    
    # ls
    elif args.action == 'ls':
        res = send_command(address, 'ls')
    
    # add
    elif args.action == 'add':
        res = send_command(address, 'add', args.command)
    
    # del
    elif args.action == 'del':
        res = send_command(address, 'del', args.number)

    print(res)

if __name__ == '__main__':
    client(get_args())
