try:
    import socket, jobs, ctypes, start
    from pathlib import Path
    from modules.privilege_deescalation import priv_deescalation
    from modules.daemonizer import Daemonizer
    from modules.logger_config import logger
    from modules.my_socket import MySocket

except ImportError as e:
    raise ImportError(f"Module import failed: {e}")

is_first = True

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

def autostart():
    jobs.load_conf()
    jobs_name = []
    for jobname in jobs.total_jobs:
        if jobs.total_jobs[jobname].autostart is True:
            jobs_name.append(jobname)
    if jobs_name:
        start.start_jobs(jobs_name=jobs_name)

if __name__ == '__main__':
    priv_deescalation(target_user='hkrifa', proc='taskmasterd')
    Daemon = Daemonizer()
    autostart()
    serversocket = MySocket(socket.gethostname(), 4442, 'server')
    try:
        while True:
            data_received: str = ""
            try:
                clientsocket, address = serversocket.socket.accept()
                logger.log(f'[taskmasterd]: connection from {address} has been established!', 'info')
                clientsocket.sendall(bytes("Welcome\n!", "utf-8"))
                while True:
                    data_received = recv_data(clientsocket=clientsocket)
                    if not data_received:
                        break
                    if data_received:
                        jobs.init_jobs(data_received=data_received, clientsocket=clientsocket)
                clientsocket.close()
            except OSError as e:
                logger.log(f'[taskmasterd]: unexpected error occurred in function [ main ]', 'error')
            except TypeError as e:
                logger.log(f'[taskmasterd]: unexpected error occurred in function [ main ]', 'error')
            except KeyboardInterrupt:
                break
    except Exception as err:
        logger.log(f'[taskmasterd]: unexpected error occurred in function [ main ] {err} ', 'error')
    finally:
        serversocket.socket.close()
        logger.log("[taskmasterd]: daemon shutdown", 'info')