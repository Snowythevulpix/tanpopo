import customtkinter as tk
import os
import requests
import json
from PIL import Image, ImageTk
from io import BytesIO, StringIO
from dotenv import load_dotenv
import tkinter.filedialog
import re
import subprocess
import CTkListbox
import base64

#--------------- Sub-Folder Imports
from sub.mpv import *
from sub.check_and_create_files import *
from sub.file_location import *
from Authwindow import *

os.system("cls")
print("loading Tanpopo... please wait")

check_and_create_files()
load_dotenv()


class AnimeViewer:
    def __init__(self, master):
        self.master = master
        self.master.title("Tanpopo")
        self.master.configure(fg_color="#121212")

        self.screen_width = self.master.winfo_screenwidth()
        self.screen_height = self.master.winfo_screenheight()

        self.toplevel_window = None

        barrier_size = 50
        barrier_width = self.screen_width - 2 * barrier_size
        barrier_height = self.screen_height - 2 * barrier_size

        self.main_frame = tk.CTkFrame(
            self.master, width=barrier_width, height=barrier_height, fg_color="#121212"
        )
        self.main_frame.place(x=barrier_size, y=barrier_size)

        #Left and Right Seperation (Avatar, Watching | Buttons)
        self.top_frame = tk.CTkFrame(self.master, fg_color="#123459")
        self.top_frame.grid(row=0, sticky="new")
        self.top_frame.columnconfigure(0, weight=8)  # Column 0 gets 80% of the space
        self.top_frame.columnconfigure(1, weight=2)
        self.bottom_frame = tk.CTkFrame(self.master, fg_color="#947436")
        self.bottom_frame.grid(row=1)

        self.avatar_frame = tk.CTkFrame(self.top_frame, fg_color="#025492")
        self.avatar_frame.grid(row=0, column=0, pady=15, padx=15, sticky="nw")

        self.button_frame = tk.CTkFrame(self.top_frame, fg_color="#772317", height=555)
        self.button_frame.grid(row=0, column=1, pady=15, padx=15, sticky="nw")


        self.watching_frame = tk.CTkFrame(self.bottom_frame, fg_color="#932547")
        self.watching_frame.grid(row=1, column=0, pady=15, padx=15, sticky="w")
        self.watching_frame.rowconfigure(0, weight=3)  # Column 0 gets 80% of the space
        self.watching_frame.rowconfigure(1, weight=7)


        try:
            #AVATAR
            self.base64_data = os.getenv("ANILIST_AVATAR_64")
            decoded_data = base64.b64decode(self.base64_data)
            self.image = Image.open(BytesIO(decoded_data))
            self.im = tk.CTkImage(dark_image=self.image, size=(111, 111))
            self.avatar_label = tk.CTkLabel(self.avatar_frame, image=self.im, fg_color="#121212", text="")
            self.avatar_label.grid(row=0, column=0, pady=10, padx=10)
        except:
            print("Not Logged in to load images")

        self.username_label = tk.CTkLabel(
            self.avatar_frame,
            text=f"Hello {os.getenv('ANILIST_USERNAME')}!",
            fg_color="#121212",
        )
        self.username_label.grid(row=1, column=0, padx=10)

        if os.path.getsize("media_info.json") == 0:
            os.system("python api.py")

        self.display_continue_watching()

        version_text = tk.CTkLabel(self.master, text="ver 0.0.7", text_color="#FFFFFF", fg_color="#121212", padx="10")
        version_text.place(relx=1.0, rely=1.0, anchor="se")


        #---- Buttons
        self.button = tk.CTkButton(self.button_frame, text="Refresh Anilist", command=self.refresh_anilist)
        self.button.grid(row=0, column=0, pady=5, padx=5, sticky="ne", columnspan=2)

        self.auth_button = tk.CTkButton(self.button_frame, text="Refresh Authentication", command=self.refresh_authentication)
        self.auth_button.grid(row=1, column=0, pady=5, padx=5, sticky="ne", columnspan=2)

        self.mpv_button = tk.CTkButton(self.button_frame, text="Set MPV location", command=mpv_set)
        self.mpv_button.grid(row=2, column=0, pady=5, padx=5, sticky="ne")

    def open_toplevel(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ToplevelWindow()  # create window if its None or destroyed
            self.toplevel_window.wm_transient()
            self.toplevel_window.focus()
        else:
            self.toplevel_window.focus()  # if window exists focus it

    def refresh_anilist(self):
        subprocess.Popen(["python", "api.py"])
        self.master.destroy()
        subprocess.Popen(["python", "tanpopo.py"])

    def refresh_authentication(self):
        self.open_toplevel()
        ToplevelWindow.wait_window(self.toplevel_window)
        self.master.update()

    def display_continue_watching(self):
        try:
            with open("media_info.json", "r") as file:
                media_info = json.load(file)
        except FileNotFoundError:
            print("media_info.json not found.")
            return

        continue_watching_label = tk.CTkLabel(
            self.watching_frame,
            text="Continue Watching",
            fg_color="#121212",
            font=("Helvetica", 25),
        )
        continue_watching_label.grid(row=0, column=1)
        i = 0
        for info in media_info:
            i = i+1
            cover_url = info.get("CoverImage")
            if cover_url:
                response = requests.get(cover_url)
                if response.status_code == 200:
                    cover_image = Image.open(BytesIO(response.content))
                    cover_image = cover_image.resize(
                        (100, 150), resample=Image.BILINEAR
                    )
                    cover_image_tk = ImageTk.PhotoImage(cover_image)

                    cover_label = HoverLabel(
                        self.watching_frame, image=cover_image_tk, fg_color="#121212", text=""
                    )
                    cover_label.image = cover_image_tk
                    cover_label.bind(
                        "<Enter>",
                        lambda event, name=info["Titles"].get("Romaji"): self.show_name(
                            event, name
                        ),
                    )
                    cover_label.bind("<Leave>", self.hide_name)
                    cover_label.bind(
                        "<Button-1>",
                        lambda event, id=info.get(
                            "ID"
                        ), anime_info=info: self.choose_episode(id, anime_info),
                    )
                    cover_label.bind("<Motion>", self.move_name)
                    cover_label.grid(row=1, column=i)
            else:
                print(f"No cover image found for {info.get('Title')}.")

    def show_name(self, event, name):
        self.name_label = tk.CTkLabel(
            self.master, text=name, fg_color="#121212", font=("Helvetica", 10)
        )
        self.name_label.place(x=event.x_root, y=event.y_root)

    def move_name(self, event):
        if hasattr(self, "name_label"):
            self.name_label.place(x=event.x_root, y=event.y_root)

    def hide_name(self, event):
        if hasattr(self, "name_label"):
            self.name_label.destroy()

    def fetch_current_episode(self, username, anime_id):
        query = """
        query ($username: String, $animeId: Int) {
          Media(id: $animeId) {
            title {
              english
            }
            episodes
          }
          MediaListCollection(userName: $username, type: ANIME) {
            lists {
              entries {
                mediaId
                progress
              }
            }
          }
        }
        """
        variables = {"username": username, "animeId": anime_id}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            response = requests.post(
                "https://graphql.anilist.co",
                json={"query": query, "variables": variables},
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            if "errors" in data:
                print("AniList API Error:", data["errors"])
                return None, None
            media_info = data["data"]["Media"]
            episodes = media_info.get("episodes", None)
            lists = data["data"]["MediaListCollection"]["lists"]
            for lst in lists:
                for entry in lst["entries"]:
                    if entry["mediaId"] == anime_id:
                        return entry["progress"], episodes
            return None, episodes
        except requests.exceptions.RequestException as e:
            print("Request error:", e)
            return None, None

    def choose_episode(self, anime_id, anime_info):
        self.main_frame.pack_forget()
        self.avatar_label.place_forget()
        self.button.pack_forget()
        self.auth_button.pack_forget()
        self.mpv_button.pack_forget()

        self.episode_frame = tk.CTkFrame(self.master, fg_color="#121212")
        self.episode_frame.pack(fill="both", expand=True)

        directory = self.read_file_location(anime_id)

        if not os.path.exists("series_locations.json"):
            with open("series_locations.json", "w") as file:
                json.dump({}, file)

        def browse_file():
            file_path = tkinter.filedialog.askdirectory()
            if file_path:
                with open("series_locations.json", "r+") as file:
                    data = json.load(file)
                    data[str(anime_id)] = file_path
                    file.seek(0)
                    json.dump(data, file, indent=4)
                update_file_location()

        def update_file_location():
            directory = self.read_file_location(anime_id)
            if directory:
                file_location_label.configure(text=f"File Location: {directory}")
            else:
                file_location_label.configure(text="File Location: Not set")

        browse_button = tk.CTkButton(
            self.episode_frame, text="Set anime file location", command=browse_file
        )
        browse_button.pack(pady=10)

        file_location_label = tk.CTkLabel(
            self.episode_frame, text="File Location: Not set", fg_color="#121212"
        )
        file_location_label.pack(pady=10)
        update_file_location()

        back_button = tk.CTkButton(
            self.episode_frame, text="Back", command=self.show_main_frame
        )
        back_button.pack(pady=10)

        self.listbox = CTkListbox.CTkListbox(
            self.episode_frame, width=200, height=400, fg_color="#121212"
        )
        self.listbox.pack(pady=10)

        username = os.getenv("ANILIST_USERNAME")

        if not username:
            print("ANILIST_USERNAME not found in .env")
            return

        current_episode, episodes = self.fetch_current_episode(username, anime_id)

        if directory:
            files = os.listdir(directory)
            files.sort()

            episode_number = current_episode or 0
            episode_range = range(episode_number, len(files) + 1)

            episodes = [file for file in files if re.search(r"\d+", file)]
            self.listbox.insert("end", *episodes)

            self.listbox.bind("<Double-1>", lambda event: self.play_video(directory))

            if current_episode:
                self.listbox.select_set(current_episode - 1)
                self.listbox.see(current_episode - 1)

        if not directory or not episodes:
            print("No directory found or episodes available")

    def play_video(self, directory):
        selected_indices = self.listbox.curselection()
        if selected_indices:
            selected_episode = self.listbox.get(selected_indices[0])

            file_path = os.path.join(directory, selected_episode)
            if os.path.exists(file_path):
                mpv_location = self.get_mpv_location()
                if mpv_location:
                    subprocess.Popen([mpv_location, file_path])
                else:
                    print("mpv location not set")
            else:
                print(f"{file_path} does not exist")

    def get_mpv_location(self):
        try:
            with open("preferences.json", "r") as file:
                data = json.load(file)
                return data.get("mpv_location")
        except FileNotFoundError:
            return None

    def show_main_frame(self):
        self.episode_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True)
        self.avatar_label.place(x=20, y=20)  # Display the avatar label again
        self.button.pack(side="top", anchor="ne", pady=20,
                         padx=20)  # Ensure the refresh button is packed at the correct position
        self.auth_button.pack(side="top", anchor="ne", pady=20,
                              padx=20)  # Ensure the authentication button is packed at the correct position


class HoverLabel(tk.CTkLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


if __name__ == "__main__":
    root = tk.CTk()
    app = AnimeViewer(root)
    root.geometry("800x600")
    root.mainloop()
