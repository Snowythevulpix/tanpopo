import os
import requests
from dotenv import load_dotenv
import json
import re

# Load environment variables from .env file
load_dotenv()

# Function to clear the JSON file
def clear_json_file(file_path):
    with open(file_path, 'w') as f:
        f.truncate(0)
        print("Cleared JSON file.")

# Function to fetch anime information from AniList
def fetch_anime_info(anime_ids):
    base_url = "https://graphql.anilist.co"
    headers = {"Content-Type": "application/json"}

    anime_info = []

    for anime_id in anime_ids:
        query = '''
        query ($id: Int) {
          Media(id: $id, type: ANIME) {
            id
            title {
              romaji
              english
              native
            }
            status
            averageScore
            genres
            description(asHtml: false)
            coverImage {
              extraLarge
            }
          }
        }
        '''

        variables = {
            "id": anime_id
        }

        response = requests.post(base_url, headers=headers, json={"query": query, "variables": variables})
        data = response.json()

        if "errors" in data:
            print(f"Error fetching data for anime with ID {anime_id}: {data['errors'][0]['message']}")
        else:
            anime_info.append(data['data']['Media'])

    return anime_info

# Function to filter out unwanted text from anime description
def filter_description(description):
    # Remove <br> tags and other HTML markup
    filtered_description = re.sub(r'<.*?>', '', description)
    return filtered_description

# Function to rearrange data alphabetically by anime title
def sort_data_alphabetically(data):
    sorted_data = sorted(data, key=lambda x: x['Title'])
    return sorted_data

# Function to format and store anime information in a JSON file
def format_and_store_info(media_info):
    formatted_info = {
        "ID": media_info["id"],
        "Title": media_info["title"]["romaji"],
        "CoverImage": media_info.get("coverImage", {}).get("extraLarge", "N/A"),
        "Description": filter_description(media_info.get("description", "No description available"))
    }

    filename = "media_info.json"
    data = []

    # Read existing data from the JSON file if it exists
    if os.path.exists(filename):
        with open(filename, "r") as file:
            try:
                data = json.load(file)
            except json.decoder.JSONDecodeError:
                # Handle the case where the file is empty or malformed
                pass

    # Check if the entry already exists in the data
    entry_exists = any(entry["ID"] == formatted_info["ID"] for entry in data)

    # If the entry doesn't exist, append it to the data
    if not entry_exists:
        data.append(formatted_info)

        # Sort data alphabetically
        sorted_data = sort_data_alphabetically(data)

        # Write the updated data back to the JSON file
        with open(filename, "w") as file:
            json.dump(sorted_data, file, indent=4)

        print("Formatted information stored successfully.")
    else:
        print("Entry already exists in the JSON file. Skipping.")

# Function to retrieve media list collection from AniList
def get_media_list_collection(access_token, user_id):
    def fetch_media_list(status):
        query = '''
        query ($userId: Int, $type: MediaType, $status: MediaListStatus) {
          MediaListCollection (userId: $userId, type: $type, status: $status) {
            lists {
              entries {
                media {
                  id
                  title {
                    romaji
                  }
                }
                status
              }
            }
          }
        }
        '''

        variables = {
            'userId': user_id,
            'type': 'ANIME',
            'status': status
        }

        response = requests.post('https://graphql.anilist.co', json={'query': query, 'variables': variables}, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if 'errors' in data:
                print("Error occurred:")
                for error in data['errors']:
                    print(error['message'])
            else:
                return data['data']['MediaListCollection']
        else:
            print(f"Request failed with status code {response.status_code}")
            print(f"Response content: {response.content.decode('utf-8')}")
            return None

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    current_shows = fetch_media_list('CURRENT')
    rewatched_shows = fetch_media_list('REPEATING')

    if current_shows and rewatched_shows:
        return current_shows, rewatched_shows
    else:
        return None, None

# Fetch the AniList access token and user ID from the environment variables
access_token = os.getenv('ANILIST_ACCESS_TOKEN')
user_id = os.getenv('ANILIST_ID')

if access_token and user_id:
    current_shows, rewatched_shows = get_media_list_collection(access_token, user_id)
    if current_shows and rewatched_shows:
        # Clear the JSON file before refreshing it
        clear_json_file("media_info.json")

        # Proceed with fetching anime information and storing it in the JSON file
        anime_ids = set()  # Using a set to store unique anime IDs

        for media_list in current_shows['lists']:
            for entry in media_list.get('entries', []):
                anime_id = entry['media']['id']
                if anime_id not in anime_ids:  # Check if anime ID has not been printed before
                    anime_ids.add(anime_id)  # Add anime ID to the set

        for media_list in rewatched_shows['lists']:
            for entry in media_list.get('entries', []):
                anime_id = entry['media']['id']
                if anime_id not in anime_ids:  # Check if anime ID has not been printed before
                    anime_ids.add(anime_id)  # Add anime ID to the set

        # Fetch anime info for the collected IDs
        anime_info = fetch_anime_info(anime_ids)
        for info in anime_info:
            # Store anime info in JSON file
            format_and_store_info(info)

        print("AniList refresh successful.")
    else:
        print("No data retrieved for currently watching or rewatched shows.")
else:
    print("AniList access token or user ID not found in the environment variables.")
