import sys
import readline
import yaml
from modules.complete import SimpleCompleter

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

treatment_funcs = {
    'start': start,
    'stop': stop,
    'pid': get_server_pid,
    'exit': exit, 
    'quit': quit,
    'reload': reload,
}
readline.parse_and_bind('tab: complete')
completer = SimpleCompleter(list(treatment_funcs.keys()))
readline.set_completer(completer.complete)

def treatment(line: str) -> int:
    space = line.find(' ')
    full_cmd = dict()
    cmds_list = list(treatment_funcs.keys())
    if space != -1:
        if line[0:space] not in cmds_list:
            return print_errors(line=line)
    elif line not in cmds_list:
        return print_errors(line=line)
    args = line.split()
    cmd = args.pop(0)
   
    return treatment_funcs[cmd]()

if __name__ == '__main__':
    while True:
        line = input("taskmaster> ")
        readline.set_auto_history(True)
        treatment(line=line)
