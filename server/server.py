from modules.JobConf import JobConf
from pathlib import Path
import os, sys, yaml
from time import sleep
from multiprocessing import Process, current_process
from modules.Daemonizer import Daemonizer
from modules.LoggerHandler import LoggerHandler
from modules.MySocket import MySocket
import socket
# export PYTHONPATH="/home/hkrifa/Bureau/taskmaster:$PYTHONPATH"

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

if __name__ == '__main__':
    try:
        logger = LoggerHandler(actual_path('/logs/logs.file'))
    except Exception as err:
        print(err)
    # Daemon = Daemonizer()
    # logger.log('Daemon ok', 'info')
    serversocket = MySocket(socket.gethostname(), 4242, 'bind')
    while True:
        (clientsocket, address) = serversocket.accept()
        logger.log(f'Connection from {address} has been established!', 'info')
        msg = "Welcome to the server!"
        clientsocket.send(bytes(msg, "utf-8"))
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