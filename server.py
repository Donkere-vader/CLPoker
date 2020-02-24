import socket
import json
import os
import threading
import datetime
import random

IP = '0.0.0.0'
PLAYING_CARDS = []
for color in ['heart', 'tiles', 'clovers', 'pikes']:
    for i in range(0, 14):
        num = i
        PLAYING_CARDS.append({
            "color":color,
            "value":num
        })

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
        self.stake = stake
        self.call_to = self.stake

    def start(self):
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
            data = c.recv(1024)
            if not data:
                continue
            data = json.loads(data.decode("utf-8"))
            if data['type'] == 'move':
                if data['move'] == 'call':
                    pass
                if data['move'] == 'check':
                    pass
                if data['move'] == 'raise':
                    pass

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
        tables = []
        for table in self.tables:
            tables.append({
                "name":table.name,
                "port":table.port
            })
        data = {
            "type":"tables",
            "tables":tables
        }
        self.connections.append(c)
        c.send(bytes(json.dumps(data), "utf-8"))
        self.log.append(f"\u001b[32m[{self.get_time()}]\u001b[0m New connection with {a}")
        self.console_out()
        while True:
            try:
                data = c.recv(1024)
                if not data:
                    continue
                data = json.loads(data.decode("utf-8"))
            except ConnectionResetError:
                self.log.append(f"\u001b[31m[{self.get_time()}]\u001b[0m Lost connection with {a}")
                self.console_out()
                self.connections.remove(c)
                return
            if data['type'] == 'new_table':
                table_port = self.new_table(data['name'], data['stake'])d
                data = {
                    "type":"table",
                    "port":table_port
                }
                c.send(bytes(json.dumps(data), "utf-8"))
    
    def new_table(self, name, stake):
        new_table = Table(name, stake)
        self.tables.append(new_table)
        new_table.start()
        return new_table.port

    def get_time(self):
        date = datetime.datetime.now()
        time = f"{date.hour if date.hour > 9 else ('0' + str(date.hour))}:{date.minute if date.minute > 9 else ('0' + str(date.minute))} {date.day}/{date.month}/{date.year}"
        return time

    def console_out(self):
        os.system('cls')
        print_logo()
        print(f"\u001b[32m>>> SERVER ONLINE <<<\nIP: {socket.gethostbyname(socket.gethostname())}\nPORT: {self.sock.getsockname()[1]}\u001b[0m")
        print("\n[[ === TABLES === ]]")
        for table in self.tables:
            tabs = 2
            tabs -= len(table.name) // 8
            print(table.name + ("\t" * tabs) + str(table.port) + ("\t" * tabs), end="")
            if len(table.connections) > 5:
                print(f"\u001b[31m{table.connections}/6\u001b[0m")
            else:
                print(f"\u001b[32m{table.connections}/6\u001b[0m")
        print("\n[[ === LOG === ]]")
        self.log = self.log[-15:]
        for n in self.log:
            print(n)

server = server()