try:
    import readline, socket
    import readline
    import socket
    from pathlib import Path
    from modules.privilege_deescalation import priv_deescalation
    from modules.completer import Completer
    from modules.my_socket import MySocket
    from modules.logger_config import logger
except ImportError as e:
    raise ImportError(f"Module import failed: {e}")

MAGENTA = "\033[95m"
RESET = "\033[0m"

def print_errors(line:str) -> int:
    print(f'*** Unknown syntax: {line}')
    return 1

cmds_list = ['start', 'stop', 'restart', 'reload' ]

def actual_path(path: str) -> str:
    actual_path = str(Path().resolve())
    return actual_path[0:actual_path.rfind('/')] + path

def auto_completion():
    readline.parse_and_bind('tab: complete')
    completer = Completer(cmds_list)
    readline.set_completer(completer.complete)

def handle_line(line: str) -> int:
    if line:
        args = line.split()
        cmd = args.pop(0)
        if cmd in ('exit', 'quit'):
            return -1
    return 0

if __name__ == '__main__':
    priv_deescalation(proc='taskmasterctl')
    auto_completion()
    clientsocket = MySocket(socket.gethostname(), 4442, 'client')
    msg = clientsocket.receive_data()
    while True:
        try:
            line = input(f"{MAGENTA}taskmaster> {RESET}")
            readline.set_auto_history(True)
            ret = handle_line(line=line)
            if ret == 0:
                clientsocket.send_data(data=line)
            elif ret == -1:
                break
            #ready_to_read = clientsocket.nonblocking()
            #if ready_to_read:
            data = clientsocket.receive_data()
            print(data[0:len(data) - 1])
        except KeyboardInterrupt:
            break
    clientsocket.socket.close()