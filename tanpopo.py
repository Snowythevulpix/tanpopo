import tkinter as tk
import os
import requests
import json
from PIL import Image, ImageTk
from io import BytesIO
from dotenv import load_dotenv
import tkinter.filedialog
import re
import subprocess

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

        # Display user's avatar and username
        self.display_user_info()

        # Run api.py if media_info.json is empty
        if os.path.getsize("media_info.json") == 0:
            os.system("python api.py")

        # Display "Continue Watching" section
        self.display_continue_watching()

        version_text = tk.Label(root, text="ver 0.1.1", fg="#FFFFFF", bg="#121212")
        version_text.place(relx=1.0, rely=1.0, anchor="se")

        # Create a button to refresh Anilist data
        self.button = tk.Button(self.master, text="Refresh Anilist", command=lambda: os.system("python api.py"))
        self.button.pack(side="top", anchor="ne", pady=20, padx=20)

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
        # Create a new window for choosing episodes
        episode_window = tk.Toplevel(self.master)
        episode_window.title(f"Choose Episode - {anime_id}")
        episode_window.configure(bg="#121212")  # Set background color

        # Get the screen width and height
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Set the window size to match the screen size
        episode_window.geometry(f"{screen_width}x{screen_height}+0+0")

        # Check if the folder path for the anime exists in series_locations.json
        with open("series_locations.json", "r") as file:
            data = json.load(file)
            if str(anime_id) in data:
                anime_folder = data[str(anime_id)]
                # Scan the folder for available episodes
                available_episodes = []
                for file_name in os.listdir(anime_folder):
                    # Extract the episode number from the filename
                    file_episode_number_match = re.search(r'\d+', file_name)
                    if file_episode_number_match:
                        file_episode_number = int(file_episode_number_match.group())
                        available_episodes.append(file_episode_number)
                available_episodes.sort()  # Sort the episode numbers
            else:
                print(f"No directory found for anime ID {anime_id} in series_locations.json.")
                episode_window.destroy()  # Close the window if folder path is not found
                return

        # Function to handle episode selection and play
        def play_episode():
            selected_episode_index = episode_listbox.curselection()
            if selected_episode_index:
                selected_episode = episode_listbox.get(selected_episode_index[0])
                print(f"Playing Episode {selected_episode}")
                # Find the file path of the selected episode
                file_path = os.path.join(anime_folder, f"Episode {selected_episode:02d}.mp4")  # Assuming the episodes are named like "Episode 01.mp4"
                if os.path.exists(file_path):
                    print(f"File found: {file_path}")  # Print the file location
                    # Play the selected episode with MPV
                    mpv_location = data.get("mpv_location")
                    if mpv_location:
                        try:
                            subprocess.Popen([mpv_location, file_path])
                        except FileNotFoundError:
                            print("Error: MPV not found. Make sure it's installed and added to your PATH.")
                    else:
                        print("Error: MPV location not configured.")
                else:
                    print(f"File not found for Episode {selected_episode}")

        # Create labels for episode information
        episode_label = tk.Label(episode_window, text="Choose an episode:", bg="#121212", fg="#FFFFFF", font=("Helvetica", 16))
        episode_label.pack(pady=10)

        # Create a Listbox for selecting episodes
        episode_listbox = tk.Listbox(episode_window, selectmode=tk.SINGLE, bg="#121212", fg="#FFFFFF", font=("Helvetica", 12), width=30)
        episode_listbox.pack(pady=10, padx=10)

        # Populate the Listbox with available episode options
        for episode_number in available_episodes:
            episode_listbox.insert(tk.END, f"Episode {episode_number:02d}")  # Ensure double-digit episode numbers are formatted with leading zeros

        # Button to play the selected episode
        play_button = tk.Button(episode_window, text="Play Episode", command=play_episode)
        play_button.pack(pady=10)

        # Center the episode selection window
        episode_window.update_idletasks()
        episode_window.geometry(f"+{(screen_width - episode_window.winfo_width()) // 2}+{(screen_height - episode_window.winfo_height()) // 2}")

        # Display the series location text
        series_location_label = tk.Label(episode_window, text=f"Series Location: {anime_folder}", bg="#121212", fg="#FFFFFF", font=("Helvetica", 10))
        series_location_label.pack(pady=10)

        # Button to select series location
        select_location_button = tk.Button(episode_window, text="Select Series Location", command=lambda: self.prompt_directory(anime_id))
        select_location_button.pack(pady=10)

        episode_window.mainloop()

    def prompt_directory(self, anime_id):
        directory = tk.filedialog.askdirectory(title="Select Series Location")
        if directory:
            with open("series_locations.json", "r+") as file:
                data = json.load(file)
                data[str(anime_id)] = directory
                file.seek(0)
                json.dump(data, file, indent=4)
                file.truncate()

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
    # Create the Tkinter root window
    root.state('zoomed')  # Set window state to maximized
    app = AnimeViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
