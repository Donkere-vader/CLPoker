from tkinter import Tk, Button, Entry, Frame, Label, messagebox, PhotoImage
import socket
import json
import threading

__version__ = "0.9"


class Client:
    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((ip, port))
        except socket.gaierror:
            messagebox.showerror("ERROR", "Not existing server")
            game.main()
        self.cards = []

    def start(self):
        self.set_name()
        while True:
            try:
                data = self.sock.recv(1024)
                if not data:
                    continue
                data = json.loads(data.decode("utf-8"))
            except ConnectionResetError:
                messagebox.showerror("ERROR", "Connection to server lost...")
                game.main()
                return
            if data['type'] == 'tables':
                game.tables(data['tables'])
            elif data['type'] == "table_port":
                game.join_table(data['port'])
            elif data['type'] == "cards":
                self.cards = data['cards']
            elif data['type'] == "table_info":
                game.middle_cards = data['middle_cards']
                game.players = data['players']
                game.flop = data['flop']
                game.river = data['river']
                game.stake = data['stake']
                game.a = data['a']
                game.table_name = data['table_name']
                game.table()
            elif data['type'] == 'game_start':
                game.cards = data['cards']
                game.middle_cards = data['middle_cards']
                game.players = data['players']
                game.on_turn = data['on_turn']
                game.call_to = 0
                for p in data['players']:
                    game.players[p]['bet'] = data['players'][p]['bet']
                    if data['players'][p]['bet'] > game.call_to:
                        game.call_to = data['players'][p]['bet']
                game.table()
                game.update()
            elif data['type'] == 'update':
                game.call_to = 0
                for p in data['bets']:
                    game.players[p]['bet'] = data['bets'][p]
                    if data['bets'][p] > game.call_to:
                        game.call_to = data['bets'][p]
                if 'flop' in data:
                    game.flop = True
                    game.middle_cards.append(data['flop'])
                if 'river' in data:
                    game.river = True
                    game.middle_cards.append(data['flop'])
                print("flop:", game.flop)
                print("river:", game.river)
                print(game.middle_cards, "\n")
                game.on_turn = data['on_turn']
                game.update()
            elif data['type'] == 'msg':
                mThread = threading.Thread(target=messagebox.showinfo, args=("msg", data['msg']))
                mThread.daemon = True
                mThread.start()

    def set_name(self):
        data = {
            "type": "name",
            "name": game.name
        }
        self.sock.send(bytes(json.dumps(data), "utf-8"))


class Game:
    def __init__(self):
        self.root = Tk()
        self.root.title("CLPoker")
        self.images = []
        self.main()
        self.client = None
        self.name = "player"
        self.pot = 0
        self.middle_cards = []
        self.players = {}
        self.a = ""
        self.flop = False
        self.river = False
        self.stake = 0
        self.cards = []
        self.ready = False
        self.on_turn = ""
        self.call_to = 0
        self.table_name = ""

    def send(self, data):
        self.client.sock.send(bytes(json.dumps(data), "utf-8"))

    def clear_window(self, window):
        for i in window.winfo_children():
            i.destroy()

    def main(self):
        self.clear_window(self.root)
        Label(
            text="CL Poker",
            font='arial 20'
        ).grid()
        Label(
            text="Connect to a poker server",
            font='arial 12'
        ).grid()
        Label(
            text="",
            font='arial 12'
        ).grid()
        Label(
            text="Server ip:",
            anchor='nw',
            justify="left",
            font='arial 12'
        ).grid(sticky='w')
        ip_entry = Entry(
            font='arial 20',
            width=20
        )
        ip_entry.grid()
        Label(
            text="Server port:",
            anchor='nw',
            justify="left",
            font='arial 12'
        ).grid(sticky='w')
        port_entry = Entry(
            font='arial 20',
            width=20
        )
        port_entry.grid()
        Button(
            text='Connect',
            font='arial 20',
            width=18,
            command=lambda ip_entry=ip_entry, port_entry=port_entry: self.connect(ip_entry, port_entry)
        ).grid()

    def connect(self, ip_entry, port_entry):
        ip = ip_entry.get()
        try:
            port = int(port_entry.get())
        except ValueError:
            messagebox.showerror("ERROR", "Invalid port")
        self.server_port = port
        self.cThread = threading.Thread(target=self.start_connection, args=(ip, port))
        self.cThread.daemon = True
        self.cThread.start()
        self.clear_window(self.root)

    def tables(self, tables):
        self.clear_window(self.root)
        Label(
            text=f"Connected to server {self.client.sock.getsockname()[0]}:{self.client.sock.getsockname()[1]}",
            bg='green',
            fg="white"
        ).grid()
        Label(
            text="Your name",
            font='arial 12'
        ).grid()

        name_entry = Entry(
            font='arial 20'
        )
        name_entry.grid()

        Label(
            text="Choose a table",
            font='arial 20'
        ).grid()
        for table in tables:
            Button(
                text=table['name'],
                width=20,
                font='arial 20',
                comman=lambda port=table['port'], name_entry=name_entry: self.join_table(port, name_entry=name_entry)
            ).grid()

        table_options_frame = Frame()
        table_options_frame.grid()

        Button(
            master=table_options_frame,
            text="New table",
            command=lambda name_entry=name_entry: self.new_table(name_entry)
        ).grid(row=0, column=0)

        Button(
            master=table_options_frame,
            text="Refresh",
            command=lambda data={"type": "refresh_tables"}: self.send(data)
        ).grid(row=0, column=1)

    def join_table(self, port, name_entry=None):
        if name_entry:
            self.name = name_entry.get()[:10]
        ip = self.client.sock.getsockname()[0]
        self.client.sock.shutdown(socket.SHUT_WR)
        del self.client
        self.cThread = threading.Thread(target=self.start_connection, args=(ip, port))
        self.cThread.daemon = True
        self.cThread.start()

    def start_connection(self, ip, port):
        self.client = Client(ip, port)
        self.client.start()

    def new_table(self, name_entry):
        self.name = name_entry.get()[:10]
        self.clear_window(self.root)
        Label(
            text="New table",
            font="arial 20"
        ).grid()

        Label(
            text="Table name",
            anchor='nw',
            justify="left",
            font='arial 12'
        ).grid(sticky='w')
        name_entry = Entry(
            font='arial 20',
            width=20
        )
        name_entry.grid()
        Label(
            text="Table stake",
            anchor='nw',
            justify="left",
            font='arial 12'
        ).grid(sticky='w')
        stake_entry = Entry(
            font='arial 20',
            width=20
        )
        stake_entry.grid()
        Button(
            text='Create',
            font='arial 20',
            width=18,
            command=lambda name_entry=name_entry, stake_entry=stake_entry: self.create_new_table(name_entry, stake_entry)
        ).grid()

    def create_new_table(self, name_entry, stake_entry):
        name = name_entry.get()
        if len(name) == 0 or len(name) > 16:
            messagebox.showerror("ERROR", "Table name must be between 1 or 16 letters.")
            return
        try:
            stake = int(stake_entry.get())
        except ValueError:
            messagebox.showerror("ERROR", "stake must be a number")
            return

        data = {
            "type": "new_table",
            "name": name,
            "stake": stake
        }
        self.send(data)

    def table(self):
        self.images = []
        self.clear_window(self.root)
        self.menu_frame = Frame()
        self.menu_frame.grid()
        self.game_frame = Frame()
        self.game_frame.grid()
        self.options_frame = Frame()
        self.options_frame.grid()

        Button(
            master=self.menu_frame,
            text='Leave',
            font='arial 15',
            command=self.leave_table
        ).grid(row=0, column=0)

        Label(
            master=self.menu_frame,
            text=f"\t\tTable: {self.table_name}\t\tStake: {self.stake}",
            font='arial 15'
        ).grid(row=0, column=1)

        self.players_frame = Frame(master=self.game_frame)
        self.players_frame.grid()

        for idx, player in enumerate(self.players):
            if player == self.a:
                continue
            self.players[player]['label'] = Label(
                master=self.players_frame,
                font='arial 20',
                text=f"{self.players[player]['name']}\n€ {self.players[player]['money']}\nBet: {self.players[player]['bet']}"
            )
            self.players[player]['label'].grid(row=0, column=idx)

        self.table_frame = Frame(master=self.game_frame)
        self.table_frame.grid()

        self.middle_cards_frame = Frame(master=self.table_frame)
        self.middle_cards_frame.grid()

        for i in range(5):
            if i <= len(self.middle_cards) - 1:
                img = PhotoImage(file=f"cards/{self.middle_cards[i]['color']}{self.middle_cards[i]['value']}.png")
            else:
                img = PhotoImage(file="cards/card_back.png")
            self.images.append(img)
            img_lbl = Label(
                master=self.middle_cards_frame,
                image=self.images[len(self.images)-1]
            )
            img_lbl.grid(row=0, column=i)

        self.pot_frame = Frame(master=self.table_frame)
        self.pot_frame.grid()

        self.pot_label = Label(
            master=self.pot_frame,
            font='arail 25',
            text=f"Pot: € {self.pot}"
        )
        self.pot_label.grid()

        self.user_frame = Frame(master=self.game_frame)
        self.user_frame.grid()

        self.user_cards_frame = Frame(master=self.user_frame)
        self.user_cards_frame.grid()
        for idx, card in enumerate(self.cards):
            img = PhotoImage(file=f"cards/{card['color']}{card['value']}.png")
            self.images.append(img)
            img_lbl = Label(
                master=self.user_cards_frame,
                image=self.images[len(self.images)-1]
            )
            img_lbl.grid(row=0, column=idx)

        self.user_info = Frame(master=self.user_frame)
        self.user_info.grid()

        self.user_info_lbl = Label(
            master=self.user_cards_frame,
            font='arial 25'
        )
        self.user_info_lbl.grid(columnspan=2)

        self.ready_button = Button(
            master=self.options_frame,
            text="ready" if not self.ready else "cancel",
            fg='white',
            font='arial 30',
            width=17,
            bg='green' if not self.ready else "grey",
            command=lambda: self.ready_up()
        )
        self.ready_button.pack(side="right")

    def ready_up(self):
        self.ready = not self.ready
        data = {
            "type": "ready",
            "ready": self.ready
        }
        self.send(data)
        self.ready_button.config(
            text="ready" if not self.ready else "cancel",
            bg='green' if not self.ready else "grey"
        )

    def update(self):
        self.clear_window(self.options_frame)

        if self.on_turn:
            Button(
                master=self.options_frame,
                text="Raise",
                font='arial 15',
                bg='green',
                fg='white',
                width=20,
                command=self.raise_bet
            ).pack(side="right")

            self.raise_entry = Entry(
                master=self.options_frame,
                font='arial 17',
                width=20,
            )
            self.raise_entry.insert(0, "20")
            self.raise_entry.pack(side="right")
            Button(
                master=self.options_frame,
                text="Check" if self.players[self.a]['bet'] >= self.call_to else f"Call {self.players[self.a]['bet'] - self.call_to}",
                font='arial 15',
                bg='green',
                fg='white',
                width=20,
                command=self.call
            ).pack(side='right')

            Button(
                master=self.options_frame,
                text="Fold",
                font='arial 15',
                bg='green',
                fg='white',
                width=20,
                command=self.fold
            ).pack(side='right')

        for player in self.players:
            if player == self.a:
                continue
            self.players[player]['label'].config(
                text=f"{self.players[player]['name']}\n€ {self.players[player]['money']}\nBet: {self.players[player]['bet']}"
            )

        self.pot_label.config(text=f"Pot: € {self.pot}")
        self.user_info_lbl.config(text=f"{self.name}\nMoney: €{self.players[self.a]['money']}\nBet: €{self.players[self.a]['bet']}")

        self.clear_window(self.middle_cards_frame)
        for i in range(5):
            if i <= len(self.middle_cards) - 1:
                img = PhotoImage(file=f"cards/{self.middle_cards[i]['color']}{self.middle_cards[i]['value']}.png")
            else:
                img = PhotoImage(file="cards/card_back.png")
            self.images.append(img)
            img_lbl = Label(
                master=self.middle_cards_frame,
                image=self.images[len(self.images)-1]
            )
            img_lbl.grid(row=0, column=i)

    def call(self):  # if check call will mean check
        data = {
            "type": "move",
            "move": "call"
        }
        self.send(data)

    def raise_bet(self):
        try:
            amount = int(self.raise_entry.get()) + self.call_to
        except ValueError:
            messagebox.showerror("ERROR", "Raise amount is invalid")
            return
        if self.players[self.a]['bet'] + amount > self.players[self.a]['money']:
            amount = self.players[self.a]['money']
        data = {
            "type": "move",
            "move": "raise",
            "amount": amount
        }
        self.send(data)

    def fold(self):
        data = {
            "type": "move",
            "move": "fold"
        }
        self.send(data)

    def leave_table(self):
        ip = self.client.sock.getsockname()[0]
        self.client.sock.shutdown(socket.SHUT_WR)
        del self.client
        self.cThread = threading.Thread(target=self.start_connection, args=(ip, self.server_port))
        self.cThread.daemon = True
        self.cThread.start()


game = Game()
game.root.mainloop()

# TODO UPDATE handle al the incomming data and update the game variables and update the screen
