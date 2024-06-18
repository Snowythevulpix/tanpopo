import json


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
