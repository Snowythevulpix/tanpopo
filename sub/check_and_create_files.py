import os
import json

def check_and_create_files():
    files_to_create = ["media_info.json", "series_locations.json", "preferences.json", ".env"]

    for file_name in files_to_create:
        if not os.path.exists(file_name):
            # Create the file
            with open(file_name, "w") as file:
                # If it's preferences.json, create an empty dictionary
                if file_name == "preferences.json":
                    json.dump({}, file)
                # Otherwise, create an empty list
                elif file_name == ".env":
                    # Do not write anything to .env, just create the empty file
                    pass
                else:
                    json.dump([], file)

    # Check if .env file is empty
    env_file = '.env'

    if os.path.exists(env_file):
        with open(env_file, 'r') as file:
            content = file.read().strip()

        if not content:
            print(".env is empty, running auth.py")
            # Execute auth.py
            os.system('python auth.py')
        else:
            print(".env is not empty, skipping auth.py")
    else:
        print(".env file does not exist")

