from modules.JobConf import JobConf
from pathlib import Path
import os, sys, yaml
from time import sleep
from multiprocessing import Process, current_process
from modules.Daemonizer import Daemonizer
from modules.LoggerHandler import LoggerHandler
from modules.MySocket import MySocket
import socket, select
# export PYTHONPATH="/home/hkrifa/Desktop/taskmaster:$PYTHONPATH"

# def worker():
#     while True:
#         process = current_process()
#         print(f'Daemon process: {process.daemon}')
#         print("PID : ")
#         print(os.getpid())
#         sleep(2)

def actual_path(path: str) -> str:
    actual_path = str(Path().resolve())
    return actual_path[0:actual_path.rfind('/')] + path

def recv_data(clientsocket: int):
    data_received = str()
    while True:
        client_data = clientsocket.recv(16).decode('utf-8')
        if not client_data:
            break
        data_received += client_data
        if '\n' in data_received:
            break
    return data_received[0:len(data_received) - 1]

if __name__ == '__main__':
    try:
        logger = LoggerHandler(actual_path('/logs/logs.file'))
        serversocket = MySocket(socket.gethostname(), 4242, 'server')

        while True:
            data_received = str()
            try:
                clientsocket, address = serversocket.accept()
                logger.log(f'Connection from {address} has been established!', 'info')
                data = "Welcome to the server!\n"
                clientsocket.sendall(bytes(data, "utf-8"))
                while True:
                    data_received = recv_data(clientsocket=clientsocket)
                    if not data_received:
                        break
                    if data_received == 'start toto':
                        clientsocket.sendall(bytes(data, 'utf-8'))
                        print(clientsocket.fileno())
                    logger.log(f'Données reçues: {data_received}', 'info')
                clientsocket.close()
            except OSError as e:
                logger.log(str(e), 'error')
            except KeyboardInterrupt:
                break
    except Exception as err:
        logger.log(err, 'error')
    finally:
        serversocket.close()
        logger.log("Server shutdown", 'info')
    # process = Process(target=worker, daemon=True)
    # process.start()
    # process.join()
    # jobs = dict()
    # actual_path = str(Path().resolve())
    # fileconf_path = actual_path[0:actual_path.rfind('/')] + '/conf/conf.yml'
    # try:
    #     with open(fileconf_path, 'r') as file:
    #         yaml_content = yaml.safe_load(file)
    #         for key, value in yaml_content.items():
    #             jobConf = JobConf(value, key)
    #             jobs[key] = jobConf
    # except Exception as error:
    #     print(error)