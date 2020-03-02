import socket
import json
import os
import threading
import datetime
import random

__version__ = "0.9"

LOG_LENGTH = 15
STARTINGMONEY = 1000
IP = '0.0.0.0'
PLAYING_CARDS = []
for color in ['hearts', 'tiles', 'clovers', 'pikes']:
    for i in range(1, 14):
        num = i
        PLAYING_CARDS.append({
            "color": color,
            "value": num
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
        self.playing_users = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((IP, 0))
        self.port = self.sock.getsockname()[1]
        self.sock.listen(1)
        self.on_turn = 0
        self.pot = 0
        self.stake = stake
        self.call_to = self.stake
        self.on_stake = None
        self.parent_server = server
        self.middle_cards = []
        self.occupied_cards = []
        self.game_started = False
        self.flop = False
        self.river = False
        self.winners = []
        self.won_by = ""

    def start(self):
        while True:
            c, a = self.sock.accept()
            cThread = threading.Thread(target=self.handler, args=(c, a))
            cThread.daemon = True
            cThread.start()
            self.connections.append(c)

    def handler(self, c, a):
        a = f"{a[0]}:{a[1]}"
        self.connected_users[a] = {
            "c": c,
            "name": "Player",
            "in_game": False,
            "money": STARTINGMONEY,
            "cards": [],
            "bet": 0
        }
        self.parent_server.Log(f"\u001b[32m[{get_time()}]\u001b[0m {a} Connected to table {self.name}")
        players = {}
        for player in self.playing_users:
            players[player] = {
                "name": self.playing_users[player]['name'],
                "a": self.playing_users[player]['a']
            }
        bets = {}
        for user in self.connected_users:
            bets[user] = self.connected_users[user]['bet']
        data = {
            "type": "table_info",
            "middle_cards": self.middle_cards,
            "players": players,
            "flop": self.flop,
            "river": self.river,
            "stake": self.stake,
            "a": a,
            "table_name": self.name
        }
        self.connected_users[a]['c'].send(bytes(json.dumps(data), "utf-8"))
        while True:
            try:
                data = c.recv(1024)
            except ConnectionResetError:
                data = None
            if not data:
                del self.connected_users[a]
                self.parent_server.Log(f"\u001b[31m[{get_time()}]\u001b[0m {a} Left table {self.name}")
                if a in self.playing_users:
                    del self.playing_users[a]
                if len(self.connected_users) == 0:
                    del self.parent_server.tables[self.parent_server.tables.index(self)]
                    self.parent_server.Log(f"\u001b[31m[{get_time()}]\u001b[0m Table {self.name} offline")
                    del self
                    return
                # update table info at users? that someone left? TODO
                return

            data = json.loads(data.decode("utf-8"))
            if data['type'] == 'move':
                if data['move'] == 'call':
                    if self.playing_users[a]['money'] < self.call_to - self.playing_users[a]['bet']:
                        self.playing_users['bet'] += self.playing_users[a]['money']
                        self.playing_users[a]['money'] = 0
                    else:
                        self.playing_users[a]['bet'] = self.call_to
                        self.playing_users[a]['money'] -= self.call_to - self.playing_users[a]['bet']
                if data['move'] == 'raise':
                    amount = data['amount']
                    self.call_to += amount
                    self.playing_users[a]['bet'] += amount
                    self.playing_users[a]['money'] -= amount
                    self.parent_server.Log(f"{self.playing_users[a]['name']} has betted {self.playing_users[a]['bet']} and has {self.playing_users[a]['money']} EUR left")

                next_round = True
                bet = 0
                for p in self.playing_users:
                    if bet == 0:
                        bet = self.playing_users[p]['bet']
                    if self.playing_users[p]['bet'] != bet:
                        next_round = False

                self.parent_server.Log(f"bet: {bet}, next_round: {next_round}, bet == self.stake: {bet == self.stake}, self.on_turn == self.on_stake: {self.on_turn == self.on_stake}")
                if (next_round and bet == self.stake and self.on_turn == self.on_stake) or (next_round and bet != self.stake):
                    if not self.flop:
                        self.flop = True
                    else:
                        self.river = True
                        self.winners, self.won_by = self.check_winners()
                        self.end_of_round()
                self.parent_server.Log(f"self.flop: {self.flop}\nself.river: {self.river}")
                self.on_turn = self.get_next_in_dict(self.on_turn, self.playing_users)
                if data['move'] == 'fold':
                    del self.playing_users[a]
                    if len(self.playing_users) < 2:
                        self.winners = [next(iter(self.playing_users))]
                        self.won_by = "being the last one "
                        self.end_of_round()
                self.update_users()

            if data['type'] == 'name':
                if data['name'] != '':
                    self.connected_users[a]['name'] = data['name']
                    self.parent_server.console_out()

            if data['type'] == 'ready':
                self.connected_users[a]['in_game'] = data['ready']
                if not self.game_started:
                    ready = True
                    for user in self.connected_users:
                        if self.connected_users[user]['in_game'] == False:
                            ready = False
                            break
                    if ready and len(self.connected_users) > 1:
                        self.start_game()

    def get_next_in_dict(self, cur, dct):
        nxt_one = False
        for i in dct:
            if nxt_one:
                return i
            elif i == cur:
                nxt_one = True
        return next(iter(dct))

    def end_of_round(self):
        for p in self.winners:
            self.connected_users[p]['money'] = self.pot // len(self.winners)
        self.pot = 0
        msg = f"{self.connected_users[self.winners[0]]['name']} won with a {self.won_by}"
        self.parent_server.Log(f"winners: {self.winners} len(winners): {len(self.winners)}")
        if len(self.winners) > 1:
            msg = ""
            for idx, w in enumerate(self.winners):
                if idx < len(self.winners) - 1:
                    msg += f"{self.connected_users[w]['name']}, "
                elif idx == len(self.winners) - 1:
                    msg += self.connected_users[w]['name']
                else:
                    msg += f"{self.connected_users[w]['name']} & "
                msg += f" won with a {self.won_by}"
        for c in self.connected_users:
            data = {
                "type": "msg",
                "msg": msg
            }
            self.connected_users[c]['c'].send(bytes(json.dumps(data), "utf-8"))
        self.start_game()

    def start_game(self):
        self.pot = 0
        self.parent_server.Log(f"\u001b[31m[{get_time()}]\u001b[0m Starting game at table {self.name} {self.port}")
        self.game_started = True
        self.playing_users = {}
        for user in self.connected_users:
            if self.connected_users[user]['in_game']:
                self.playing_users[user] = self.connected_users[user]
        self.shuffle()
        self.on_stake = self.get_next_in_dict(self.on_stake, self.playing_users)
        self.connected_users[self.on_stake]['money'] -= self.stake
        self.pot += self.stake
        self.connected_users[self.on_stake]['bet'] = self.stake
        self.on_turn = self.get_next_in_dict(self.on_stake, self.playing_users)
        players = {}
        for user in self.playing_users:
            players[user] = {
                "name": self.playing_users[user]['name'],
                "bet": self.playing_users[user]['bet'],
                "money": self.playing_users[user]['money']
            }
        for user in self.connected_users:
            data = {
                "type": "game_start",
                "cards": self.connected_users[user]['cards'],
                "middle_cards": self.middle_cards[:3],
                "players": players,
                "on_turn": True if user == self.on_turn else False
            }
            self.connected_users[user]['c'].send(bytes(json.dumps(data), "utf-8"))

    def update_users(self):  # send all the data to the users
        bets = {}
        for user in self.playing_users:
            bets[user] = self.playing_users[user]['bet']
        for user in self.connected_users:
            data = {
                "type": "update",
                "on_turn": True if user == self.on_turn else False,
                "pot": self.pot,
                "bets": bets
            }
            if self.flop:
                data['flop'] = self.middle_cards[3]
            if self.river:
                data['river'] = self.middle_cards[4]
            self.connected_users[user]['c'].send(bytes(json.dumps(data), "utf-8"))

    def shuffle(self):
        self.occupied_cards = []
        self.middle_cards = []
        for i in range(5):
            card = random.choice(PLAYING_CARDS)
            while card in self.occupied_cards:
                card = random.choice(PLAYING_CARDS)
            self.middle_cards.append(card)
            i += 1
        for user in self.playing_users:
            cards = []
            for i in range(2):
                card = random.choice(PLAYING_CARDS)
                while card in self.occupied_cards:
                    card = random.choice(PLAYING_CARDS)
                cards.append(card)
            self.connected_users[user]['cards'] = cards

    def check_winners(self):
        winners = []
        highest_score = 0  # from high card (1) to straight flush (9)
        highest_card = 0
        won_by = ''
        for user in self.connected_users:
            cards = self.middle_cards
            cards += self.connected_users[user]['cards']
            card_values = [card['value'] for card in cards]
            card_values.sort()
            card_colors = [card['color'] for card in cards]

            # check for high card
            if highest_score <= 1:
                for card in self.connected_users[user]['cards']:
                    if card['value'] == highest_card:
                        winners.append(user)
                        highest_score = 1
                        won_by = 'Highest card'
                    elif card['value'] > highest_card:
                        highest_card = card['value']
                        winners = [user]
                        highest_score = 1
                        won_by = 'Highest card'

            # pairs
            if highest_score <= 3:
                pairs = []
                for card in card_values:
                    if card_values.count(card) >= 2:
                        if card not in pairs:
                            pairs.append(card)
                if (len(pairs) == 1 and highest_score <= 2) or (len(pairs) >= 2 and highest_score <= 3):
                    if highest_card == max(pairs):
                        winners.append(user)
                    if highest_card < max(pairs):
                        winners = [user]
                        highest_card = max(pairs)
                    if len(pairs) == 1:
                        highest_score = 2
                        won_by = 'Pair'
                    else:
                        highest_score = 3
                        won_by = 'Two pairs'

            # three of a kind
            three_of_a_kind = 0
            if highest_score <= 4:
                for card in card_values:
                    if card_values.count(card) == 3:
                        if highest_score < 4 or highest_card < card:
                            highest_score = 4
                            highest_card = card
                            winners = [user]
                        else:
                            winners.append(user)
                        won_by = 'Three of a kind'
                        three_of_a_kind = card

            # straight
            if highest_score <= 5:
                past_value = min(card_values)
                straight = True
                for i in range(1, 5):
                    if min(card_values) + i != past_value + 1:
                        straight = False
                        break
                if straight:
                    if highest_score < 5 or highest_card < max(card_values):
                        highest_score = 5
                        winners = [user]
                        highest_card = max(card_values)
                    else:
                        winners.append(user)
                    won_by = 'Straight'

            # flush
            flush = False
            if highest_score <= 6:
                for card in card_colors:
                    if card_colors.count(card) == 5:
                        if highest_score < 6 or highest_card < max(card_values):
                            winners = [user]
                            highest_score = 6
                            highest_card = max(card_values)
                        else:
                            winners.append(user)
                        flush = True
                        won_by = 'Flush'

            # full house
            if highest_score <= 7:
                if (len(pairs) == 1 and three_of_a_kind and three_of_a_kind not in pairs) or (three_of_a_kind and len(pairs) >= 2):
                    if highest_score < 7 or highest_card < max(card_values):
                        winners = [user]
                        highest_score = 7
                        highest_card = max(card_values)
                    else:
                        winners.append(user)
                    won_by = 'Full house'

            # four of a kind
            if highest_score <= 8:
                for card in card_values:
                    if card_values.count(card) == 4:
                        if highest_score < 8 or highest_card < max(card_values):
                            highest_score = 4
                            highest_card = max(card_values)
                            winners = [user]
                        else:
                            winners.append(user)
                        won_by = 'Four of a kind'

            # check for straight flush
            if highest_score <= 9:
                if straight and flush:
                    self.parent_server.Log("\u001b[32mSOMEONE GOT A FRICKIN STRAIGHT FLUSH!!!!!\u001b[0m")
                    from tkinter import messagebox
                    messagebox.showinfo("WAATT", "SOMEONE GOT A FRICKIG STRAIGHT FLUSH!!!")
                    if highest_score < 9 or highest_card < max(card_values):
                        highest_score = 9
                        highest_card = max(card_values)
                        winners = [user]
                    else:
                        winners.append(user)
                    won_by = 'Straight fkn flush'
        return winners, won_by


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
        self.log = self.log[-LOG_LENGTH:]
        self.console_out()

    def handler(self, c, a):
        tables = []
        for table in self.tables:
            tables.append({
                "name": table.name,
                "port": table.port
            })
        data = {
            "type": "tables",
            "tables": tables
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
                    "type": "table_port",
                    "port": table_port
                }
                c.send(bytes(json.dumps(data), "utf-8"))
            if data['type'] == 'refresh_tables':
                tables = []
                for table in self.tables:
                    tables.append({
                        "name": table.name,
                        "port": table.port
                    })
                data = {
                    "type": "tables",
                    "tables": tables
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
        for n in self.log:
            print(n)


server = Server()
