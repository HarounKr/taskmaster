import socket

class MySocket:
    def __init__(self, host, port, type):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if type == 'conn':
            self.sock.connect((host, port))
        else:
            self.sock.bind((host, port))
            self.sock.listen(5)

    def accept(self):
        return self.sock.accept()

    def send_msg(self, msg):
        sent = self.sock.send(bytes(msg, "utf-8"))
        if sent == 0:
            raise RuntimeError("socket connection broken")

    def receive_msg(self):
        full_msg = self.sock.recv(4096)
        return full_msg.decode()