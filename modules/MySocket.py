import socket
import sys
import select

class MySocket:
    def __init__(self, host, port, type):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            if type == 'client':
                self.sock.connect((host, port))
            elif type == 'server':
                self.sock.bind((host, port))
                self.sock.listen()
        except OSError as e:
            sys.stderr.write(f"{e.errno} ({e.strerror})\n")
            sys.exit(1)

    def accept(self):
        return self.sock.accept()
    
    def getsocket(self):
        return self.sock
    
    def send_data(self, data):
        try:
            self.sock.sendall(bytes(data, "utf-8"))
        except OSError as e:
            sys.stderr.write(f"socket connection broken: {e.errno} ({e.strerror})\n")

    def receive_data(self):
        try:
            full_data = self.sock.recv(10000).decode()
        except OSError as e:
            sys.stderr.write(f"{e.errno} ({e.strerror})\n")
        finally:
            return full_data
        
    def close(self):
        self.sock.close()
    
    def nonblocking(self):
        ready_to_read, _, _ = select.select([self.sock], [], [], 0.2)
        return ready_to_read
    
    def fd(self):
        return self.sock.fileno()