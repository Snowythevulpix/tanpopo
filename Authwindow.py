import customtkinter
import os
import subprocess

from api import entry
from sub.exchange_code_for_token import *


class ToplevelWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("400x300")

        if not os.path.exists('.env'):
            with open('.env', 'w') as f:
                pass
        get_authorization_code()
        self.title("Authorization Code")

        self.label = customtkinter.CTkLabel(self, text="Enter Authorization Code:")
        self.label.pack(padx=20, pady=20)

        entry = customtkinter.CTkEntry(self)
        print(entry.get())
        entry.pack()

        self.submit_button = customtkinter.CTkButton(self, text="Submit", command=self.submit_authorization_code)
        self.submit_button.pack()

    def submit_authorization_code(self):
        print("1")
        print(entry.get())
        authorization_code = entry.get()
        if authorization_code:
            access_token = exchange_code_for_token(authorization_code.strip())
            if access_token:
                print("Access token:", access_token)
                print("Success")
                self.destroy()
            else:
                print("Authorization failed.")
            self.destroy()
        else:
            print("Please enter the authorization code.")

