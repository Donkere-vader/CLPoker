import socket
import json
import os
import threading
import datetime

IP = '0.0.0.0'

def print_logo():
    print("""\u001b[31m
   ██████╗██╗         ██████╗  ██████╗ ██╗  ██╗███████╗██████╗ 
  ██╔════╝██║         ██╔══██╗██╔═══██╗██║ ██╔╝██╔════╝██╔══██╗
  ██║     ██║         ██████╔╝██║   ██║█████╔╝ █████╗  ██████╔╝
  ██║     ██║         ██╔═══╝ ██║   ██║██╔═██╗ ██╔══╝  ██╔══██╗
  ╚██████╗███████╗    ██║     ╚██████╔╝██║  ██╗███████╗██║  ██║
   ╚═════╝╚══════╝    ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝                                                       
\u001b[0m\t\t\tBy CLSoftSolutions (C)\n""")

class Table:
    def __init__(self, name, stake):
        self.name = name
        self.connections = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((IP, 0))
        self.port = self.sock.getsockname()[1]
        self.sock.listen(1)
        self.on_turn = 0
        self.pot = 0
        self.stake = 10
        self.call_to = self.stake

        while True:
            c, a = self.sock.accept()
            cThread = threading.Thread(target=self.handler, args=(c, a))
            cThread.daemon = True
            cThread.start()
            self.connections.append(c)

    def handler(self, c, a):
        server.log.append(f"\u001b[31m[+]\u001b[0m {a} Connected to table {self.name}")
        server.console_out()
        while True:
            data = json.loads(self.sock.recv(1024).decode("utf-8"))
            if data['type'] == 'move':
                if data['move']

class server:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((IP, 0))
        self.tables = []
        self.connections = []
        self.log = []
        self.sock.listen(1)
        self.log.append(f"\u001b[32m[{self.get_time()}]\u001b[0m SERVER ONLINE ({socket.gethostbyname(socket.gethostname())}, {self.sock.getsockname()[1]})")
        self.console_out()


        while True:
            c, a = self.sock.accept()
            cThread = threading.Thread(target=self.handler, args=(c, a))
            cThread.daemon = True
            cThread.start()
            self.connections.append(c)

    def handler(self, c, a):
        data = {
            "type":"tables",
            "tables":self.tables
        }
        c.send(bytes(json.dumps(data), "utf-8"))
        self.log.append("\u001b[32m[{self.get_time()}]\u001b[0m New connection with {a}")
        self.console_out()
        while True:
            try:
                data = json.loads(self.sock.recv(1024).decode("utf-8"))
            except ConnectionResetError:
                self.log.append("\u001b[31m[{self.get_time()}]\u001b[0m Lost connection with {a}")
                self.console_out()
            if data['type'] == 'new_table':
                data['name']
    
    def get_time(self):
        date = datetime.datetime.now()
        time = f"{date.hour if date.hour > 9 else ('0' + str(date.hour))}:{date.minute if date.minute > 9 else ('0' + str(date.minute))} {date.day}/{date.month}/{date.year}"
        return time

    def console_out(self):
        os.system('cls')
        print_logo()
        print(f"\u001b[32m>>> SERVER ONLINE <<<\nIP: {socket.gethostbyname(socket.gethostname())}\nPORT: {self.sock.getsockname()[1]}\u001b[0m\n")
        print("\n[ TABLES ]")
        for table in self.tables:
            tabs = 2
            tabs -= len(table.name) // 8
            print(table.name + ("\t" * tabs), end="")
            if len(table.connections) > 5:
                print(f"\u001b[31m{table.connections}/6\u001b[0m")
            else:
                print(f"\u001b[32m{table.connections}/6\u001b[0m")
        print("\n[[ === LOG === ]]")
        self.log = self.log[-15:]
        for n in self.log:
            print(n)

server = server()