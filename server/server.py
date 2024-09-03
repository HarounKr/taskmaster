try:
    from pathlib import Path
    import os, sys, yaml
    from time import sleep
    from modules.daemonizer import Daemonizer
    from modules.logger_handler import LoggerHandler
    from modules.my_socket import MySocket
    import socket, select
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
    logger = LoggerHandler(actual_path('/logs/logs.file'))
    # Daemon = Daemonizer()
    serversocket = MySocket(socket.gethostname(), 4442, 'server')
    try:
        while True:
            data_received: str = ""
            try:
                clientsocket, address = serversocket.socket.accept()
                logger.log(f'Connection from {address} has been established!', 'info')
                data = "Welcome to the server!\n"
                print(clientsocket.fileno())
                clientsocket.sendall(bytes(data, "utf-8"))
                while True:
                    data_received = recv_data(clientsocket=clientsocket)
                    print(data_received)
                    if not data_received:
                        break
                    if data_received == 'start toto':
                        clientsocket.sendall(bytes(data, 'utf-8'))
                        print(clientsocket.fileno())
                    init_jobs(data_received=data_received, clientsocket=clientsocket)
                clientsocket.close()
            except OSError as e:
                logger.log(str(e), 'error')
            except TypeError as e:
                print(e)
            except KeyboardInterrupt:
                break
    except Exception as err:
        logger.log(err, 'error')
    finally:
        serversocket.socket.close()
        logger.log("Server shutdown", 'info')
    # process = Process(target=worker, daemon=True)
    # process.start()
    # process.join()
    # jobs = dict()
   