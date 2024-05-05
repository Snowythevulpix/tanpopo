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

        # Get the screen width and height
        screen_width = episode_window.winfo_screenwidth()
        screen_height = episode_window.winfo_screenheight()

        # Set the window size to match the screen size
        episode_window.geometry(f"{screen_width}x{screen_height}+0+0")

        # Load episode information for the selected anime
        episode_count = anime_info.get("EpisodeCount")
        if episode_count is None:
            # Prompt the user to enter the actual number of episodes
            episode_count = int(input(f"Enter the number of episodes for {anime_info['Title']}: "))
            anime_info["EpisodeCount"] = episode_count
            # Update the JSON file with the new episode count
            with open("media_info.json", "w") as file:
                json.dump([anime_info], file, indent=4)

        # Check if series_locations.json exists, if not create an empty one
        if not os.path.exists("series_locations.json"):
            with open("series_locations.json", "w") as file:
                json.dump({}, file)

        # Function to open file explorer and select file location
        def browse_file():
            file_path = tkinter.filedialog.askdirectory()
            if file_path:
                # Save anime ID and file location in series_locations.json
                with open("series_locations.json", "r+") as file:
                    data = json.load(file)
                    data[str(anime_id)] = file_path
                    file.seek(0)
                    json.dump(data, file, indent=4)

        # Button to open file explorer
        browse_button = tk.Button(episode_window, text="Select File Location", command=browse_file)
        browse_button.pack(pady=10)

        # Function to handle episode selection and play
        def play_episode():
            selected_episode_index = episode_listbox.curselection()
            if selected_episode_index:
                selected_episode = episode_listbox.get(selected_episode_index[0])
                print(f"Searching for episode: {selected_episode}")
                # Extract the episode number from the selected episode string
                selected_episode_number = int(re.search(r'\d+', selected_episode).group())  # Extract episode number and convert to integer
                print(f"Episode number extracted from selected episode: {selected_episode_number}")
                # Search for the file in the selected file location
                file_path = None
                with open("series_locations.json", "r") as file:
                    data = json.load(file)
                    if str(anime_id) in data:
                        directory = data[str(anime_id)]
                        print(f"Searching in directory: {directory}")
                        for file_name in os.listdir(directory):
                            print(f"Checking file: {file_name}")
                            # Extract the episode number from the filename
                            file_episode_number_match = re.search(r'\d+', file_name)
                            if file_episode_number_match:
                                file_episode_number = int(file_episode_number_match.group())  # Extract episode number and convert to integer
                                print(f"Episode number extracted from file: {file_episode_number}")
                                if selected_episode_number == file_episode_number:
                                    file_path = os.path.join(directory, file_name)
                                    print(f"File found: {file_path}")  # Print the file location
                                    break
                        if not file_path:
                            print(f"Could not find Episode {selected_episode_number} in the selected file location.")
                    else:
                        print(f"No directory found for anime ID {anime_id} in series_locations.json.")

                if file_path is None:
                    print(f"Could not find Episode {selected_episode_number} in the selected file location.")
                else:
                    print(f"Playing {selected_episode}: {file_path}")
                    # Play the selected episode with MPV
                    mpv_location = data.get("mpv_location")
                    if mpv_location:
                        try:
                            subprocess.Popen([mpv_location, file_path])
                        except FileNotFoundError:
                            print("Error: MPV not found. Make sure it's installed and added to your PATH.")
                    else:
                        print("Error: MPV location not configured.")

        # Create labels for episode information
        episode_label = tk.Label(episode_window, text="Choose an episode:", bg="#121212", fg="#FFFFFF", font=("Helvetica", 16))
        episode_label.pack(pady=10)

        # Create a Listbox for selecting episodes
        episode_listbox = tk.Listbox(episode_window, selectmode=tk.SINGLE, bg="#121212", fg="#FFFFFF", font=("Helvetica", 12), width=30)
        episode_listbox.pack(pady=10, padx=10)

        # Populate the Listbox with episode options
        for i in range(1, episode_count + 1):
            episode_listbox.insert(tk.END, f"Episode {i:02d}")  # Ensure double-digit episode numbers are formatted with leading zeros

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
    # Create the Tkinter root window
    root.state('zoomed')  # Set window state to maximized
    app = AnimeViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
