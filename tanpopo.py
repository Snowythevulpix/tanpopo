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

os.system("cls")
print("loading Tanpopo... please wait")

# Load environment variables from .env file
load_dotenv()

class AnimeViewer:
    def __init__(self, master):
        self.master = master
        self.master.title("Tanpopo")  # Change the window title to "Tanpopo"
        self.master.configure(bg="#121212")  # Set background color to dark gray

        # Get screen width and height
        self.screen_width = self.master.winfo_screenwidth()
        self.screen_height = self.master.winfo_screenheight()

        # Calculate the size of the barrier
        barrier_size = 50
        barrier_width = self.screen_width - 2 * barrier_size
        barrier_height = self.screen_height - 2 * barrier_size

        # Create a frame to contain the main content
        self.main_frame = tk.Frame(self.master, width=barrier_width, height=barrier_height, bg="#121212")  # Set frame background color
        self.main_frame.place(x=barrier_size, y=barrier_size)

        # Display user's avatar and username
        self.display_user_info()

        # Run api.py if media_info.json is empty
        if os.path.getsize("media_info.json") == 0:
            os.system("python api.py")

        # Display "Continue Watching" section
        self.display_continue_watching()

        version_text = tk.Label(self.master, text="ver 0.0.6", fg="#FFFFFF", bg="#121212")
        version_text.place(relx=1.0, rely=1.0, anchor="se")

        # Create a button to refresh anilist data
        self.button = tk.Button(self.master, text="Refresh Anilist", command=self.refresh_anilist)
        self.button.pack(side="top", anchor="ne", pady=20, padx=20)

    def refresh_anilist(self):
        # Start the Anilist refresh process in a separate subprocess
        subprocess.Popen(["python", "api.py"])
        
        # Close the current Tkinter window
        self.master.destroy()
        
        # Reopen the application
        subprocess.Popen(["python", "tanpopo.py"])

        # Create a button to refresh authentication data
        self.button = tk.Button(self.master, text="refresh authentication", command=self.refresh_authentication)
        self.button.pack(side="top", anchor="ne", pady=20, padx=20)

    def refresh_authentication(self):
        # Start the authentication refresh process in a separate subprocess
        subprocess.Popen(["python", "auth.py"])
        
        # Close the current Tkinter window
        self.master.destroy()
        
        # Reopen the application
        subprocess.Popen(["python", "tanpopo.py"])



    def display_user_info(self):
        # Download user's avatar image
        avatar_url = os.getenv("ANILIST_AVATAR")
        if avatar_url:
            response = requests.get(avatar_url)
            if response.status_code == 200:
                avatar_image = Image.open(BytesIO(response.content))
                avatar_image = avatar_image.resize((100, 100), resample=Image.BILINEAR)  # Resize image if needed #type: ignore
                self.user_avatar = ImageTk.PhotoImage(avatar_image)
                self.avatar_label = tk.Label(self.master, image=self.user_avatar, bg="#121212")  # Set label background color #type: ignore
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
        continue_watching_label = tk.Label(self.main_frame, text="Continue Watching", bg="#121212", fg="#FFFFFF", font=("Helvetica", 25))
        continue_watching_label.pack(pady=(50, 20), padx=(100, 100))  # Adjusted padx and pady here

        # Display cover images with hover effect and name display
        for info in media_info:
            # Load cover image
            cover_url = info.get("CoverImage")
            if cover_url:
                response = requests.get(cover_url)
                if response.status_code == 200:
                    cover_image = Image.open(BytesIO(response.content))
                    cover_image = cover_image.resize((100, 150), resample=Image.BILINEAR) #type: ignore
                    cover_image_tk = ImageTk.PhotoImage(cover_image)

                    # Create label for cover image
                    cover_label = HoverLabel(self.main_frame, image=cover_image_tk, bg="#121212")
                    cover_label.image = cover_image_tk #type: ignore
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

    def fetch_current_episode(self, username, anime_id):
        query = '''
        query ($username: String, $animeId: Int) {
          Media(id: $animeId) {
            title {
              romaji
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
        '''
        variables = {
            'username': username,
            'animeId': anime_id
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        try:
            response = requests.post(
                'https://graphql.anilist.co',
                json={'query': query, 'variables': variables},
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            if 'errors' in data:
                print("AniList API Error:", data['errors'])
                return None, None
            media_info = data['data']['Media']
            episodes = media_info.get('episodes', None)
            lists = data['data']['MediaListCollection']['lists']
            for lst in lists:
                for entry in lst['entries']:
                    if entry['mediaId'] == anime_id:
                        return entry['progress'], episodes
            return None, episodes
        except requests.exceptions.RequestException as e:
            print("Request error:", e)
            return None, None

    def choose_episode(self, anime_id, anime_info):
        self.main_frame.pack_forget()
        self.avatar_label.place_forget()  # Hide the avatar when choosing an episode
        self.button.pack_forget()  # Hide the refresh button

        self.episode_frame = tk.Frame(self.master, bg="#121212")
        self.episode_frame.pack(fill="both", expand=True)

        # Get the file location from series_locations.json
        directory = read_file_location(anime_id)

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

                # Update the file location label
                update_file_location()

        # Function to update the file location label with the selected directory path
        def update_file_location():
            directory = read_file_location(anime_id)
            if directory:
                file_location_label.config(text=f"File Location: {directory}")

        # Button to open file explorer
        browse_button = tk.Button(self.episode_frame, text="Select File Location", command=browse_file)
        browse_button.pack(pady=10)

        # Label to display the selected file location
        file_location_label = tk.Label(self.episode_frame, text="", bg="#121212", fg="#FFFFFF")
        file_location_label.pack(pady=5)

        # Initialize the file location
        update_file_location()

        # Button to display file location
        update_location_button = tk.Button(self.episode_frame, text="Display File Location", command=update_file_location)
        update_location_button.pack(pady=5)

        def play_episode():
            # Initialize file_path variable
            file_path = None

            selected_episode_index = episode_listbox.curselection()
            if selected_episode_index:
                selected_episode = episode_listbox.get(selected_episode_index[0])
                print(f"Searching for episode: {selected_episode}")
                # Extract the episode number from the selected episode string
                selected_episode_number = int(re.search(r'\d+', selected_episode).group())  # type: ignore # Extract episode number and convert to integer
                print(f"Episode number extracted from selected episode: {selected_episode_number}")
                # Search for the file in the selected file location
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
        episode_label = tk.Label(self.episode_frame, text="Choose an episode:", bg="#121212", fg="#FFFFFF", font=("Helvetica", 16))
        episode_label.pack(pady=10)

        # Create a Listbox for selecting episodes
        episode_listbox = tk.Listbox(self.episode_frame, selectmode=tk.SINGLE, bg="#121212", fg="#FFFFFF", font=("Helvetica", 12), width=30)
        episode_listbox.pack(pady=10, padx=10)

        # Populate the Listbox with episode options
        if directory:
            # Get the list of episode files in the directory
            episode_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            for episode_file in episode_files:
                episode_number_match = re.search(r'\d+', episode_file)
                if episode_number_match:
                    episode_number = int(episode_number_match.group())
                    episode_listbox.insert(tk.END, f"Episode {episode_number}")

        # Fetch the current episode
        anilist_username = os.getenv('ANILIST_USERNAME')
        current_episode, total_episodes = self.fetch_current_episode(anilist_username, anime_id)
        if current_episode is not None:
            current_episode_label = tk.Label(self.episode_frame, text=f"Current Episode: {current_episode}", bg="#121212", fg="#FFFFFF", font=("Helvetica", 12))
            current_episode_label.pack(pady=10)

        # Display total episodes
        if total_episodes is not None:
            total_episodes_label = tk.Label(self.episode_frame, text=f"Total Episodes: {total_episodes}", bg="#121212", fg="#FFFFFF", font=("Helvetica", 12))
            total_episodes_label.pack(pady=10)
        else:
            error_label = tk.Label(self.episode_frame, text="Error fetching total episodes from AniList.", bg="#121212", fg="#FF0000", font=("Helvetica", 12))
            error_label.pack(pady=10)

        # Button to play the selected episode
        play_button = tk.Button(self.episode_frame, text="Play Episode", command=play_episode)
        play_button.pack(pady=10)

        # Display anime description in the top-right corner
        description_label = tk.Label(self.episode_frame, text=anime_info.get("Description", ""), bg="#121212", fg="#FFFFFF", font=("Helvetica", 12), wraplength=300)
        description_label.place(relx=1.0, rely=0.0, anchor="ne")

        # Back button to return to the main frame
        back_button = tk.Button(self.episode_frame, text="Back", command=self.show_main_frame)
        back_button.pack(pady=10)

    def show_main_frame(self):
        self.episode_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True)
        self.avatar_label.place(x=20, y=20)  # Display the avatar label again

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

# Create a new function to read the file location from series_locations.json
def read_file_location(anime_id):
    file_location = None
    try:
        with open("series_locations.json", "r") as file:
            data = json.load(file)
            file_location = data.get(str(anime_id))
    except FileNotFoundError:
        print("series_locations.json not found.")
    return file_location


def main():
    # Create the Tkinter root window
    root = tk.Tk()
    root.state('zoomed')  # Set window state to maximized
    app = AnimeViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
