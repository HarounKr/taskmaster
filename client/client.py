import sys
import readline
import yaml
import socket
import select
from modules.Completer import SimpleCompleter
from modules.MySocket import MySocket

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

funcs = {
    'start': start,
    'stop': stop,
    'pid': get_server_pid,
    'exit': exit,
    'quit': quit,
    'reload': reload,
}

def autocompletion():
    readline.parse_and_bind('tab: complete')
    completer = SimpleCompleter(list(funcs.keys()))
    readline.set_completer(completer.complete)

def handle_line(line: str) -> int:
    space = line.find(' ')
    full_cmd = dict()
    cmds_list = list(funcs.keys())
    if space != -1:
        if line[0:space] not in cmds_list:
            return print_errors(line=line)
    elif line not in cmds_list:
        return print_errors(line=line)
    args = line.split()
    cmd = args.pop(0)
   
    return funcs[cmd]()

if __name__ == '__main__':
    autocompletion()
    clientsocket = MySocket(socket.gethostname(), 4242, 'client')
    msg = clientsocket.receive_data()
    print(msg)
    while True:
        try:
            line = input("taskmaster> ")
            readline.set_auto_history(True)
            if handle_line(line=line) != 1:
                clientsocket.send_data(data=line + '\n')
            ready_to_read = clientsocket.nonblocking()
            print(ready_to_read)
            if ready_to_read:
                data = clientsocket.receive_data()
        except KeyboardInterrupt:
            clientsocket.close()
            sys.exit(130)