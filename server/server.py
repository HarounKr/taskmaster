try:
    from pathlib import Path
    import os, sys, yaml
    from time import sleep
    from modules.daemonizer import Daemonizer
    from modules.logger_config import logger
    from modules.my_socket import MySocket
    import socket
    from jobs import init_jobs
except ImportError as e:
    raise ImportError(f"Module import failed: {e}")

# export PYTHONPATH="/home/hkrifa/Desktop/taskmaster:$PYTHONPATH"

def actual_path(path: str) -> str:
    actual_path = str(Path().resolve())
    return actual_path[0:actual_path.rfind('/')] + path

def recv_data(clientsocket):
    data_received: str = ""
    while True:
        client_data = clientsocket.recv(16).decode('utf-8')
        if not client_data:
            break
        data_received += client_data
        if '\n' in data_received:
            break
    return data_received[0:len(data_received) - 1]

if __name__ == '__main__':
    
    # Daemon = Daemonizer()
    serversocket = MySocket(socket.gethostname(), 4442, 'server')
    try:
        while True:
            data_received: str = ""
            try:
                clientsocket, address = serversocket.socket.accept()
                logger.log(f'[SERVER]: connection from {address} has been established!', 'info')
                clientsocket.sendall(bytes("Welcome\n!", "utf-8"))
                while True:
                    data_received = recv_data(clientsocket=clientsocket)
                    if not data_received:
                        break
                    if data_received:
                        init_jobs(data_received=data_received, clientsocket=clientsocket)
                clientsocket.close()
            except OSError as e:
                logger.log(f'[SERVER]: unexpected error occurred in function [ main ]', 'error')
            except TypeError as e:
                logger.log(f'[SERVER]: unexpected error occurred in function [ main ]', 'error')
            except KeyboardInterrupt:
                break
    except Exception as err:
        logger.log(f'[SERVER]: unexpected error occurred in function [ main ] {err} ', 'error')
    finally:
        serversocket.socket.close()
        logger.log("[SERVER]: server shutdown", 'info')