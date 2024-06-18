import os
from io import BytesIO
import requests
import tkinter
from PIL import Image, ImageTk


def display_user_info():
    # Download user's avatar image
    avatar_url = os.getenv("ANILIST_AVATAR")
    if avatar_url:
        response = requests.get(avatar_url)
        if response.status_code == 200:
            return response.content
    else:
        print("please close the window and reopen the app")