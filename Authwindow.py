from tkinter import StringVar

import customtkinter
import os
import subprocess

from api import entry
from sub.auth_code import *


class ToplevelWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wm_iconbitmap("./favicon.ico")
        self.after(201, lambda: self.iconbitmap('favicon.ico'))
        self.geometry("200x140")
        self.minsize(200, 140)

        #---- Check Auth File and Open Browser
        if not os.path.exists('.env'):
            with open('.env', 'w') as f:
                pass
        get_authorization_code()

        #---- Start Top Level Window
        self.title("Authorization Code")

        self.label = customtkinter.CTkLabel(self, text="Enter Authorization Code:")
        self.label.pack(padx=20, pady=5)

        self.wronglabel = customtkinter.CTkLabel(self, text="")
        self.wronglabel.pack()

        self.authkey = StringVar()
        self.entry = customtkinter.CTkEntry(self, textvariable=self.authkey)
        self.entry.pack()

        self.submit_button = customtkinter.CTkButton(self, text="Submit", command=self.submit_authorization_code)
        self.submit_button.pack(pady="10")

    def submit_authorization_code(self):
        print(self.authkey.get())
        authorization_code = self.authkey.get()
        if authorization_code:
            access_token = exchange_code_for_token(authorization_code.strip())
            if access_token:
                print("Access token:", access_token)
                print("Success")
                self.destroy()
            else:
                print("Authorization failed.")
        else:
            self.wronglabel.configure(text="Paste Authentication Code", text_color="red")
