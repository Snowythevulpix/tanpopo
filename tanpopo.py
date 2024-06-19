import customtkinter as tk
import os
import requests
import json
from PIL import Image, ImageTk
from io import BytesIO
from dotenv import load_dotenv
import tkinter.filedialog
import re
import subprocess
import CTkListbox

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

        self.display_user_info()

        if os.path.getsize("media_info.json") == 0:
            os.system("python api.py")

        self.display_continue_watching()

        version_text = tk.CTkLabel(self.master, text="ver 0.0.7", text_color="#FFFFFF", fg_color="#121212", padx="10")
        version_text.place(relx=1.0, rely=1.0, anchor="se")

        self.button = tk.CTkButton(
            self.master, text="Refresh Anilist", command=self.refresh_anilist
        )
        self.button.pack(side="top", anchor="ne", pady=20, padx=20)

        self.auth_button = tk.CTkButton(
            self.master,
            text="Refresh Authentication",
            command=self.refresh_authentication,
        )
        self.auth_button.pack(side="top", anchor="ne", pady=20, padx=20)

        self.mpv_button = tk.CTkButton(
            self.master, text="Set MPV location", command=mpv_set
        )
        self.mpv_button.pack(side="top", anchor="ne", pady=20, padx=20)

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

    def display_user_info(self):
        avatar_url = os.getenv("ANILIST_AVATAR")
        if avatar_url:
            response = requests.get(avatar_url)
            if response.status_code == 200:
                avatar_image = Image.open(BytesIO(response.content))
                avatar_image = avatar_image.resize((100, 100), resample=Image.BILINEAR)
                self.user_avatar = ImageTk.PhotoImage(avatar_image)
                self.avatar_label = tk.CTkLabel(
                    self.master, image=self.user_avatar, fg_color="#121212", text=""
                )
                self.avatar_label.place(x=20, y=20)

                self.username_label = tk.CTkLabel(
                    self.master,
                    text=f"Hello {os.getenv('ANILIST_USERNAME')}!",
                    fg_color="#121212",
                )
                self.username_label.place(x=20, y=130)
        else:
            print("please close the window and reopen the app")

    def display_continue_watching(self):
        try:
            with open("media_info.json", "r") as file:
                media_info = json.load(file)
        except FileNotFoundError:
            print("media_info.json not found.")
            return

        continue_watching_label = tk.CTkLabel(
            self.main_frame,
            text="Continue Watching",
            fg_color="#121212",
            font=("Helvetica", 25),
        )
        continue_watching_label.pack(pady=(50, 20), padx=(100, 100))

        for info in media_info:
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
                        self.main_frame, image=cover_image_tk, fg_color="#121212", text=""
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
                    cover_label.pack(side="left", padx=10)
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
