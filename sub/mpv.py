import tkinter
import os
import json


def mpv_set():
    file_path = tkinter.filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
    if file_path:
        # Check if preferences.json exists, if not create an empty one
        if not os.path.exists("preferences.json"):
            with open("preferences.json", "w") as file:
                json.dump({}, file)

        # Save mpv_location in preferences.json
        with open("preferences.json", "r+") as file:
            data = json.load(file)
            data["mpv_location"] = file_path
            file.seek(0)
            json.dump(data, file, indent=4)