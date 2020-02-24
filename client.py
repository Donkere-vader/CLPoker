from tkinter import Tk, Button, Entry, Frame, Label, messagebox
import socket
import json
import threading

PLAYING_CARDS = []
for color in ['heart', 'tiles', 'clovers', 'pikes']:
    for i in range(0, 14):
        num = i
        PLAYING_CARDS.append({
            "color":color,
            "value":num
        })

class Client:
    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))

    def start(self):
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
                
class Game:
    def __init__(self):
        self.root = Tk()
        self.root.title = "CLPoker"
        self.main()
        self.client = None

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
            command= lambda ip_entry=ip_entry, port_entry=port_entry: self.connect(ip_entry, port_entry)
        ).grid()

    def connect(self, ip_entry, port_entry):
        ip = ip_entry.get()
        try:
            port = int(port_entry.get())
        except ValueError:
            messagebox.showerror("ERROR", "Invalid port")
        self.cThread = threading.Thread(target=self.start_connection, args=(ip, port))
        self.cThread.daemon = True
        self.cThread.start()
        self.clear_window(self.root)

    def tables(self, tables):
        Label(
            text=f"Connected to server {self.client.sock.getsockname()[0]}:{self.client.sock.getsockname()[1]}",
            bg='green',
            fg="white"
        ).grid()
        Label(
            text="Choose a table",
            font='arial 20'
        ).grid()
        for table in tables:
            Button(
                text=table['name'],
                width=20,
                font='arial 20',
                comman= lambda port=table['port']: self.join_table(port)
            ).grid()

    def join_table(self, port):
        self.client = Client(self.client.sock.getsockname()[0], port)
        self.client.start()

    def start_connection(self, ip, port):
        self.client = Client(ip, port)
        self.client.start()

game = Game()
game.root.mainloop()