import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
import os
import subprocess
import sys
import webbrowser
import threading
from chat_utils import S_OFFLINE, S_LOGGEDIN, S_CHATTING
from chat_utils import *
from indexer_student import *
from client_state_machine import ClientSM
from chat_server import NeuralNetworks
import socket
import json
# imports for the neural network
from flask import Flask, request, jsonify, send_from_directory
import tensorflow as tf
from PIL import Image
import io, base64, numpy as np
import os
from tensorflow import keras
from PIL import Image, ImageTk, ImageGrab

# READ THIS: before running this code, run the old_chat_server.py first to make sure it's listening thus we can log in
# READ THIS: there are three amazing neural networks models

# Constants (adjust paths as needed)
SERVER = ('127.0.0.1', 12345)  # the chat server address
APP_PY_PATH = '/Users/justinbian/PycharmProjects/hand_written_digit_recognition_CNN/app.py'

class YouAreAWizardHarry(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("You're a wizard Harry")
        self.geometry("1000x600")
        self.configure(bg="#f5f7fa")
        # self.s = None  # Placeholder for socket
        # self.client_sm = None  # Placeholder for ClientSM
        # self.username = None  # Placeholder for username
        self.chat_display = None  # Placeholder for chat display widget
        self.state_label = None  # and this is the placeholder for our state changing method
# ask for username
        self.username = simpledialog.askstring(
            "Login", "Enter your username:", parent=self
        )
        if not self.username:
            messagebox.showerror("Error", "Username required")
            self.destroy()
            return
# then let's set self.s
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.s.connect(SERVER)  # SERVER = (host, port) tuple
        except Exception as e:
            messagebox.showerror("Connection Error", f"Cannot connect: {e}")
            self.destroy()
            return
# now create an instance of ClientSM
        self.client_sm = ClientSM(self.s)
        self.client_sm.set_myname(self.username)

# here we create an instance of Server, so as to call the neural network
        self.neural_networks = NeuralNetworks()

        login_msg = json.dumps({"action": "login", "name": self.username})
        mysend(self.s, login_msg)
        resp = json.loads(myrecv(self.s))
# and here we initialize the state, to make our conditions for client_state_machine fit
        if resp.get("status") == "ok":
            self.client_sm.set_state(S_LOGGEDIN)
        else:
            messagebox.showerror("Login Failed", "Server rejected login")
            self.destroy()
            return



        self.sidebar_width = 160
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.icons = {}
        self.load_icons()
        self.create_topbar()
        self.create_sidebar()
        self.create_main_area()

    # new
    def receive_messages(self):
        while True:
            try:
                msg = myrecv(self.s)
                if msg:
                    self.client_sm.proc('', msg)
                    self.after(0, self.update_chat_display, self.client_sm.out_msg)
            except Exception as e:
                print(f"Connection error: {e}")
                break
        self.after(0, self.update_state_display)

    # new
    def update_chat_display(self, text):
        if self.chat_display:
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, text + "\n")
            self.chat_display.config(state=tk.DISABLED)
            self.chat_display.see(tk.END)

    def load_icons(self):
        icon_names = ["chat", "tools", "logo"]
        for name in icon_names:
            path = os.path.join(os.path.dirname(__file__), 'icons', f"{name}.png")
            try:
                img = Image.open(path)
                size = (40, 40) if name == "logo" else (20, 20)
                img = img.resize(size, Image.Resampling.LANCZOS)
                self.icons[name] = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Failed to load icon {name}: {e}")
                self.icons[name] = None

    def create_topbar(self):
        topbar = tk.Frame(self, height=60, bg="#3c8dbc")
        topbar.grid(row=0, column=0, columnspan=2, sticky="new")
        if self.icons.get("logo"):
            tk.Label(topbar, image=self.icons["logo"], bg="#3c8dbc").pack(side="left", padx=10)
        tk.Label(topbar, text="Swish and Flick: The Hogwarts Server System", font=("Helvetica", 21), fg="white", bg="#3c8dbc").pack(side="left")

    def create_sidebar(self):
        sidebar = tk.Frame(self, width=self.sidebar_width, bg="#ecf0f1")
        sidebar.grid(row=1, column=0, sticky="ns")
        buttons = [
            ("Chat", self.icons.get("chat"), self.show_chat),
            ("Tools", self.icons.get("tools"), self.show_tools),
            ("Hand Written Digit Recognizer Webpage Demo", None, self.launch_server)
        ]
        for label, icon, cmd in buttons:
            btn = tk.Button(
                sidebar, text=f"  {label}", image=icon, compound="left",
                command=cmd, bg="#ecf0f1", relief="flat", anchor="w"
            )
            btn.pack(fill="x", pady=5, padx=10)

    def create_main_area(self):
        self.main_area = tk.Frame(self, bg="#f5f7fa")
        self.main_area.grid(row=1, column=1, sticky="nsew")
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)
        self.content_frame = tk.Frame(self.main_area, bg="white")
        self.content_frame.grid(row=0, column=0, sticky="nsew")

    def clear_content(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

    def launch_server(self):
        def run():
            os.chdir(os.path.dirname(APP_PY_PATH))
            subprocess.call([sys.executable, APP_PY_PATH])
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        time.sleep(1)
        webbrowser.open('http://127.0.0.1:5000/')

    def show_chat(self):
        self.clear_content()
        tk.Label(self.content_frame, text="📨 Chat zone", font=("Arial", 16)).pack(pady=10)

        # here we fill in the blank space for chat_display
        self.chat_display = tk.Text(self.content_frame, state='disabled', wrap=tk.WORD, height=5)
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # and we also need something to hold on to for the state of the user
        self.state_label = tk.Label(self.content_frame, text="State: Unknown", font=("Arial", 12), anchor="w")
        self.state_label.pack(pady=(5, 0))

        # here, for further utility, we create a scrollable chat window
        self.chat_display = tk.Text(self.content_frame, state='disabled', wrap=tk.WORD, height=15)
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # here we create the input frame for entering text, which will be used as a parameter in the message entry part
        input_frame = tk.Frame(self.content_frame)
        input_frame.pack(fill=tk.X, pady=(5, 10))

        # here we also add a place for entering chat messages
        self.msg_entry = tk.Entry(input_frame)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.msg_entry.bind("<Return>", self.handle_chat)

        # Add chat buttons
        # for label in ["Chat", "Search", "Who", "Connect", "Disconnect"]:
        tk.Button(self.content_frame, text="Chat", command=self.handle_chat, width=25, height=2, bg="#f0f0f0").pack(pady=5)
        tk.Button(self.content_frame, text="Search", command=self.handle_search, width = 25, height = 2, bg = "#f0f0f0").pack(pady=5)
        tk.Button(self.content_frame, text="Check who's online (but not answering your texts 🤣)", command=self.handle_who, width = 35, height = 2, bg = "#f0f0f0").pack(pady=5)
        tk.Button(self.content_frame, text="Connect", command=self.handle_connect, width = 25, height = 2, bg = "#f0f0f0").pack(pady=5)
        tk.Button(self.content_frame, text="Disconnect", command=self.handle_disconnect, width = 25, height = 2, bg = "#f0f0f0").pack(pady=5)


    def update_state_display(self):
        names = {S_OFFLINE: 'Offline', S_LOGGEDIN: 'Logged In', S_CHATTING: 'Chatting'}
        state_name = names.get(self.client_sm.get_state(), 'Unknown')
        self.state_label.config(text=f"State: {state_name}")

    def handle_connect(self):
        peer = simpledialog.askstring("Connect", "Peer name:", parent=self)
        if not peer:
            return

        connected = self.client_sm.connect_to(peer)
        self.update_chat_display(self.client_sm.out_msg)

        if connected:
            self.client_sm.set_state(S_CHATTING)
        self.update_state_display()

    def handle_search(self):
        term = simpledialog.askstring("Search", "Search term:", parent=self)
        if not term:
            return

        self.client_sm.proc(f"?{term}", "")
        self.update_chat_display(self.client_sm.out_msg)
        self.update_state_display()

    def handle_who(self):
        self.client_sm.proc('who', '')
        self.update_chat_display(self.client_sm.out_msg)
        self.update_state_display()

    def handle_disconnect(self):
        self.client_sm.disconnect()
        self.update_chat_display(self.client_sm.out_msg)
        self.client_sm.set_state(S_LOGGEDIN)
        self.update_state_display()

    def handle_chat(self, event=None):
        msg = simpledialog.askstring("Chat", "Enter your message:", parent=self)
        if not msg:
            return

        self.client_sm.proc(msg, '')
        self.update_chat_display(self.client_sm.out_msg)
        self.update_state_display()


    def show_tools(self):
        self.clear_content()
        tk.Label(self.content_frame, text="🛠 Tools", font=("Arial", 16)).pack(pady=10)

        # Add tools buttons
        tk.Button(self.content_frame, text="Time", command=self.show_time, width=25, height=2, bg="#f0f0f0").pack(pady=5)
        tk.Button(self.content_frame, text="Get Poem", command=self.handle_poem, width=25, height=2, bg="#f0f0f0").pack(pady=5)

        # Add CNN canvas section
        tk.Label(self.content_frame, text='✍ CNN Canvas: "πlease" draw your digit', font=("Arial", 14)).pack(pady=10)
        self.canvas = tk.Canvas(self.content_frame, bg="white", width=200, height=200, relief="ridge", bd=2)
        self.canvas.pack(pady=5)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.prev_x = None
        self.prev_y = None

        # Add recognition buttons
        tk.Button(self.content_frame, text='recognize with v1', command=self.predict_drawing_v1, width=20).pack(pady=5)
        tk.Button(self.content_frame, text='recognize with v2', command=self.predict_drawing_v2, width=20).pack(pady=5)
        tk.Button(self.content_frame, text='recognize with v3', command=self.predict_drawing_v3, width=20).pack(pady=5)
        tk.Button(self.content_frame, text="clear canvas", command=self.clear_canvas, width=20).pack()

    def show_time(self):
        current_time = time.strftime("%H:%M:%S", time.localtime())
        messagebox.showinfo("Current Time", f"Current time is: {current_time}")

    def handle_poem(self):
        num = simpledialog.askinteger("Poem", "Enter sonnet number:")
        if num:
            self.get_poem(num)
            # self.send_command(num)


    def get_poem(self,p):

        obj = PIndex("AllSonnets.txt")
        print(obj)
        poem = obj.get_poem(p)
        if poem:
            messagebox.showinfo("Poem",poem)
        else:
            messagebox.showwarning("Poem","Failed to retrieve poem.")
        return poem

    # New methods from
    def paint(self, event):
        if self.prev_x and self.prev_y:
            self.canvas.create_line(self.prev_x, self.prev_y, event.x, event.y, width=5)
        self.prev_x = event.x
        self.prev_y = event.y

    def clear_canvas(self):
        self.canvas.delete("all")
        self.prev_x = None
        self.prev_y = None

    def predict_drawing_v1(self):
        # 1) Grab canvas area from the screen
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty()
        w = x + self.canvas.winfo_width()
        h = y + self.canvas.winfo_height()
        img = ImageGrab.grab((x, y, w, h)).convert('L')  # grayscale

        # 2) Resize to 28×28 and invert colors (white on black → black on white)
        img = img.resize((28, 28), Image.LANCZOS)
        arr = np.array(img).astype('float32')
        # when loading v3, only run this line
        arr = 255.0 - arr
        # when loading v1 or v2, also run this line
        arr = arr / 255.0
        arr = arr.reshape((1, 28, 28, 1))

        # 3) Predict with your CNN
        prediction = self.neural_networks.cnn_model_v1.predict(arr)[0]  # shape (10,)
        digit = int(np.argmax(prediction))
        confidence = prediction[digit]

        # 4) Show the result
        messagebox.showinfo(
            "Prediction",
            f"I think you drew a {digit}  \nConfidence: {confidence * 100:.1f}%"
        )


    def predict_drawing_v2(self):
        # 1) Grab canvas area from the screen
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty()
        w = x + self.canvas.winfo_width()
        h = y + self.canvas.winfo_height()
        img = ImageGrab.grab((x, y, w, h)).convert('L')  # grayscale

        # 2) Resize to 28×28 and invert colors (white on black → black on white)
        img = img.resize((28, 28), Image.LANCZOS)
        arr = np.array(img).astype('float32')
        # when loading v3, only run this line
        arr = 255.0 - arr
        # when loading v1 or v2, also run this line
        arr = arr / 255.0
        arr = arr.reshape((1, 28, 28, 1))

        # 3) Predict with your CNN
        prediction = self.neural_networks.cnn_model_v2.predict(arr)[0]  # shape (10,)
        digit = int(np.argmax(prediction))
        confidence = prediction[digit]

        # 4) Show the result
        messagebox.showinfo(
            "Prediction",
            f"I think you drew a {digit}  \nConfidence: {confidence * 100:.1f}%"
        )


    def predict_drawing_v3(self):
        # 1) Grab canvas area from the screen
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty()
        w = x + self.canvas.winfo_width()
        h = y + self.canvas.winfo_height()
        img = ImageGrab.grab((x, y, w, h)).convert('L')  # grayscale

        # 2) Resize to 28×28 and invert colors (white on black → black on white)
        img = img.resize((28, 28), Image.LANCZOS)
        arr = np.array(img).astype('float32')
        # when loading v3, only run this line
        arr = 255.0 - arr
        # when loading v1 or v2, also run this line
        # arr = arr / 255.0
        arr = arr.reshape((1, 28, 28, 1))

        # 3) Predict with your CNN
        prediction = self.neural_networks.cnn_model_v3.predict(arr)[0]  # shape (10,)
        digit = int(np.argmax(prediction))
        confidence = prediction[digit]

        # 4) Show the result
        messagebox.showinfo(
            "Prediction",
            f"I think you drew a {digit}  \nConfidence: {confidence * 100:.1f}%"
        )


if __name__ == "__main__":
    app = YouAreAWizardHarry()
    app.mainloop()

# so here are several things we were able to do and we were not able to do; we've made a chat system, encryption chat
# system, and the hand-written digit recognition neural network. the thing is that to instead of taking the hand-written
# digit as an input, send it to the server, call the neural network there, then send the result back to the user
# or to another user, we makes this a one-player game, where we call the neural network directly in the gui by
# clicking on the button, and return the result to the user at once, and in here there's no interaction with the server
# so this is the thing. however, the chat-system, the encryption, the neural network are all working.
# well let's leave it this way. it's not bad