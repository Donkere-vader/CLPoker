import socket
import json
import os
import threading
import datetime
import random

STARTINGMONEY = 1000
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

def get_time():
    date = datetime.datetime.now()
    time = f"{date.hour if date.hour > 9 else ('0' + str(date.hour))}:{date.minute if date.minute > 9 else ('0' + str(date.minute))} {date.day}/{date.month}/{date.year}"
    return time

class Table:
    def __init__(self, name, stake, server):
        self.name = name
        self.connections = []
        self.connected_users = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((IP, 0))
        self.port = self.sock.getsockname()[1]
        self.sock.listen(1)
        self.on_turn = 0
        self.pot = 0
        self.stake = stake
        self.call_to = self.stake
        self.on_stake = 0
        self.parent_server = server
        self.middle_cards = []
        self.occupied_cards = []

    def start(self):
        while True:
            c, a = self.sock.accept()
            cThread = threading.Thread(target=self.handler, args=(c, a))
            cThread.daemon = True
            cThread.start()
            self.connections.append(c)

    def handler(self, c, a):
        self.connected_users[a] = {
                        "c":c,
                        "name":"Player",
                        "in_game":False,
                        "money":STARTINGMONEY,
                        "cards":[],
                        "bet":0
                    }
        self.parent_server.Log(f"\u001b[32m[{get_time()}]\u001b[0m {a} Connected to table {self.name}")
        while True:
            try:
                data = c.recv(1024)
            except ConnectionResetError:
                self.parent_server.Log(f"\u001b[31m[{get_time()}]\u001b[0m {a} Left table {self.name}")
                return
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
            if data['type'] == 'name':
                self.connected_users[a]['name'] = data['name']
                self.parent_server.Log(self.connected_users)
    
    def shuffle(self):
        self.occupied_cards = []
        self.middle_cards = []
        for i in range(5):
            card = random.choice(PLAYING_CARDS)
            while card in self.occupied_cards:
                card = random.choice(PLAYING_CARDS)
            self.middle_cards.append(card)
            i += 1
        for user in self.connected_users:
            cards = []
            for i in range(2):
                card = random.choice(PLAYING_CARDS)
                while card in self.occupied_cards:
                    card = random.choice(PLAYING_CARDS)
                cards.append(card)
            self.connected_users[user]['cards'] = cards
    
    def check_winners(self):
        pass
            

class Server:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((IP, 0))
        self.tables = []
        self.connections = []
        self.log = []
        self.sock.listen(1)
        self.Log(f"\u001b[32m[{get_time()}]\u001b[0m SERVER ONLINE ({socket.gethostbyname(socket.gethostname())}, {self.sock.getsockname()[1]})")

        while True:
            c, a = self.sock.accept()
            cThread = threading.Thread(target=self.handler, args=(c, a))
            cThread.daemon = True
            cThread.start()
            self.connections.append(c)
    
    def Log(self, text):
        self.log.append(text)
        self.console_out()

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
        self.Log(f"\u001b[32m[{get_time()}]\u001b[0m New connection with {a}")
        while True:
            try:
                data = c.recv(1024)
                if not data:
                    continue
                data = json.loads(data.decode("utf-8"))
            except ConnectionResetError:
                self.Log(f"\u001b[31m[{get_time()}]\u001b[0m Lost connection with {a}")
                self.connections.remove(c)
                return
            if data['type'] == 'new_table':
                table_port = self.new_table(data['name'], data['stake'])
                data = {
                    "type":"table_port",
                    "port":table_port
                }
                c.send(bytes(json.dumps(data), "utf-8"))
    
    def new_table(self, name, stake):
        new_table = Table(name, stake, self)
        self.tables.append(new_table)
        tThread = threading.Thread(target=new_table.start)
        tThread.daemon = True
        tThread.start()
        self.Log(f"\u001b[32m[{get_time()}]\u001b[0m New table named '{name}' at {new_table.port}")
        return new_table.port

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
                print(f"\u001b[31m{len(table.connections)}/6\u001b[0m", end="")
            else:
                print(f"\u001b[32m{len(table.connections)}/6\u001b[0m", end="")
            for user in table.connected_users:
                print(f" {table.connected_users[user]['name']}", end="")
            print()
        print("\n[[ === LOG === ]]")
        self.log = self.log[-15:]
        for n in self.log:
            print(n)

server = Server()