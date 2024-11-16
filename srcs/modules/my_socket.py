try:
    import socket
    import sys
    import select
except ImportError as e:
    raise ImportError(f"Module import failed: {e}")

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
    
    @property
    def fd(self):
        return self.sock.fileno()
    
    @property
    def socket(self):
        return self.sock
    
    def send_data(self, data):
        try:
            self.sock.sendall(bytes(data + '\n', "utf-8"))
        except OSError as e:
            sys.stderr.write(f"socket connection broken: {e.errno} ({e.strerror})\n")

    def receive_data(self):
        try:
            full_data = str()
            while True:
                client_data = self.sock.recv(16).decode('utf-8')
                if not client_data:
                    break
                full_data += client_data
                if '\n' in full_data:
                    break
        except OSError as e:
            sys.stderr.write(f"{e.errno} ({e.strerror})\n")
        finally:
            return full_data
    
    def nonblocking(self):
        ready_to_read, _, _ = select.select([self.sock], [], [], 0.1)
        return ready_to_read