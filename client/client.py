import sys
import readline
import yaml
import socket
import select
from modules.completer import Completer
from modules.my_socket import MySocket

def start():
    print('start')

def stop():
    print('stop')

def get_server_pid():
    print('pid')

def reload():
    print('reload')

def print_errors(line:str) -> int:
    print(f'*** Unknown syntax: {line}')
    return 1

cmds_list = ['start', 'stop', 'pid', 'exit', 'quit', 'reload' ]

def auto_completion():
    readline.parse_and_bind('tab: complete')
    completer = Completer(cmds_list)
    readline.set_completer(completer.complete)

def handle_line(line: str) -> int:
    space = line.find(' ')

    if space != -1:
        if line[0:space] not in cmds_list:
            return print_errors(line=line)
    elif line not in cmds_list:
        return print_errors(line=line)
    args = line.split()
    cmd = args.pop(0)
    if cmd in ('exit', 'quit'):
        return -1
    return 0

if __name__ == '__main__':
    auto_completion()
    clientsocket = MySocket(socket.gethostname(), 4242, 'client')
    msg = clientsocket.receive_data()
    print(msg)
    while True:
        try:
            line = input("taskmaster> ")
            readline.set_auto_history(True)
            ret = handle_line(line=line)
            if ret == 0:
                clientsocket.send_data(data=line + '\n')
            elif ret == -1:
                break
            ready_to_read = clientsocket.nonblocking()
            if ready_to_read:
                data = clientsocket.receive_data()
                print(data)
        except KeyboardInterrupt:
            break
    clientsocket.close()

    # start nginx vogsphere docker-compose redis