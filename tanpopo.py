import tkinter as tk
from tkinter import ttk
import os
import requests
import json
from PIL import Image, ImageTk
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
root = tk.Tk()

class AnimeViewer:
    def __init__(self, master):
        self.master = master
        self.master.title("Tanpopo")  # Change the window title to "Tanpopo"
        self.master.configure(bg="#121212")  # Set background color to dark gray

        # Get screen width and height
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Calculate the size of the barrier
        barrier_size = 50
        barrier_width = screen_width - 2 * barrier_size
        barrier_height = screen_height - 2 * barrier_size

        # Create a frame to contain the image
        self.frame = tk.Frame(self.master, width=barrier_width, height=barrier_height, bg="#121212")  # Set frame background color
        self.frame.place(x=barrier_size, y=barrier_size)

        # Run api.py on load
        self.run_api()

        # Display user's avatar and username
        self.display_user_info()

        # Display "Continue Watching" section
        self.display_continue_watching()

    def run_api(self):
        os.system("python api.py")

    def display_user_info(self):
        # Download user's avatar image
        avatar_url = os.getenv("ANILIST_AVATAR")
        if avatar_url:
            response = requests.get(avatar_url)
            if response.status_code == 200:
                avatar_image = Image.open(BytesIO(response.content))
                avatar_image = avatar_image.resize((100, 100), resample=Image.BILINEAR)  # Resize image if needed
                self.user_avatar = ImageTk.PhotoImage(avatar_image)
                self.avatar_label = tk.Label(self.master, image=self.user_avatar, bg="#121212")  # Set label background color
                self.avatar_label.place(x=20, y=20)  # Position at top left corner

                # Display username
                self.username_label = tk.Label(self.master, text=f"Hello {os.getenv('ANILIST_USERNAME')}!", bg="#121212", fg="#FFFFFF")  # Set label background and text color
                self.username_label.place(x=20, y=130)  # Adjusted position for username
        else:
            print("please close the window and reopen the app")

    def display_continue_watching(self):
        # Load media info from media_info.json
        try:
            with open("media_info.json", "r") as file:
                media_info = json.load(file)
        except FileNotFoundError:
            print("media_info.json not found.")
            return

        # Display "Continue Watching" header
        continue_watching_label = tk.Label(self.frame, text="Continue Watching", bg="#121212", fg="#FFFFFF", font=("Helvetica", 25))
        continue_watching_label.pack(pady=(50, 20), padx=(100, 100))  # Adjusted padx and pady here

        # Display cover images with hover effect and name display
        for info in media_info:
            # Load cover image
            cover_url = info.get("CoverImage")
            if cover_url:
                response = requests.get(cover_url)
                if response.status_code == 200:
                    cover_image = Image.open(BytesIO(response.content))
                    cover_image = cover_image.resize((100, 150), resample=Image.BILINEAR)
                    cover_image_tk = ImageTk.PhotoImage(cover_image)

                    # Create label for cover image
                    cover_label = HoverLabel(self.frame, image=cover_image_tk, bg="#121212")
                    cover_label.image = cover_image_tk
                    cover_label.bind("<Enter>", lambda event, name=info.get("Title"): self.show_name(event, name))
                    cover_label.bind("<Leave>", self.hide_name)
                    cover_label.bind("<Button-1>", lambda event, id=info.get("ID"), anime_info=info: self.choose_episode(id, anime_info))
                    cover_label.bind("<Motion>", self.move_name)  # Added binding for mouse motion
                    cover_label.pack(side="left", padx=10)
            else:
                print(f"No cover image found for {info.get('Title')}.")

    def show_name(self, event, name):
        # Create label for anime name
        self.name_label = tk.Label(self.master, text=name, bg="#121212", fg="#FFFFFF", font=("Helvetica", 10))
        self.name_label.place(x=event.x_root, y=event.y_root)

    def move_name(self, event):
        # Move label for anime name with mouse cursor
        if hasattr(self, "name_label"):
            self.name_label.place(x=event.x_root, y=event.y_root)

    def hide_name(self, event):
        # Remove anime name label
        if hasattr(self, "name_label"):
            self.name_label.destroy()

    def choose_episode(self, anime_id, anime_info):
        # Create a new full-size window for choosing episodes
        episode_window = tk.Tk()
        episode_window_title = f"Choose Episode - {anime_id}"
        episode_window.title(episode_window_title)
        episode_window.configure(bg="#121212")

        # Pass the selected anime information to the episode selection window
        # For demonstration, let's assume the anime_info parameter contains information about the selected anime

        # Get the screen width and height
        screen_width = episode_window.winfo_screenwidth()
        screen_height = episode_window.winfo_screenheight()

        # Set the window size to match the screen size
        episode_window.geometry(f"{screen_width}x{screen_height}+0+0")

        # Load episode information for the selected anime
        # For demonstration, let's assume we have a dictionary of episodes
        # where the keys are episode numbers and the values are episode titles
        # Replace this with your actual episode information retrieval logic
        episode_info = {
            1: "Episode 1",
            2: "Episode 2",
            3: "Episode 3",
            # Add more episodes as needed
        }

        # Create labels for episode information
        episode_label = tk.Label(episode_window, text="Choose an episode:", bg="#121212", fg="#FFFFFF", font=("Helvetica", 16))
        episode_label.pack(pady=10)

        # Create a Combobox for selecting episodes
        episode_var = tk.StringVar()
        episode_combobox = ttk.Combobox(episode_window, textvariable=episode_var, values=list(episode_info.values()), state="readonly", width=30)
        episode_combobox.pack(pady=10)

        # Function to handle episode selection
        def play_episode():
            selected_episode = episode_combobox.get()
            for episode_num, episode_title in episode_info.items():
                if episode_title == selected_episode:
                    print(f"Playing {episode_title}")
                    # Add logic to play the selected episode
                    break

        # Button to play the selected episode
        play_button = tk.Button(episode_window, text="Play Episode", command=play_episode)
        play_button.pack(pady=10)

        episode_window.mainloop()


class HoverLabel(tk.Label):
    def __init__(self, master=None, **kwargs):
        tk.Label.__init__(self, master, **kwargs)
        self.default_bg = self["bg"]
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        self.config(bg="#000000")

    def on_leave(self, event):
        self.config(bg=self.default_bg)


def main():
    # Check if ANILIST_ACCESS_TOKEN exists in .env
    if not os.getenv("ANILIST_ACCESS_TOKEN"):
        # Run auth.py to acquire the access token
        os.system("python auth.py")

    # Create the Tkinter root window
    root.state('zoomed')  # Set window state to maximized
    app = AnimeViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
