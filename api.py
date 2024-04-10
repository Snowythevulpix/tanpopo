import os
import requests
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

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
            episodes
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

def format_and_store_info(media_info, episode_count):
    formatted_info = {
        "ID": media_info["id"],
        "Title": media_info["title"]["romaji"],
        "EpisodeCount": episode_count,
        "CoverImage": media_info.get("coverImage", {}).get("extraLarge", "N/A")
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

        # Write the updated data back to the JSON file
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)

        print("Formatted information stored successfully.")
    else:
        print("Entry already exists in the JSON file. Skipping.")

def get_media_list_collection(access_token, user_id):
    query = f'''
    query {{
      MediaListCollection (userId: {user_id}, type: ANIME, status: CURRENT) {{
        lists {{
          entries {{
            media {{
              id
              title {{
                romaji
              }}
            }}
          }}
        }}
      }}
    }}
    '''

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.post('https://graphql.anilist.co', json={'query': query}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
            print("Error occurred:")
            for error in data['errors']:
                print(error['message'])
        else:
            media_list_collection = data['data']['MediaListCollection']
            return media_list_collection
    else:
        print(f"Request failed with status code {response.status_code}")
        print(f"Response content: {response.content.decode('utf-8')}")
        return None

# Fetch the AniList access token and user ID from the environment variables
access_token = os.getenv('ANILIST_ACCESS_TOKEN')
user_id = os.getenv('ANILIST_ID')

if access_token and user_id:
    media_list_collection = get_media_list_collection(access_token, user_id)
    if media_list_collection:
        print("Media List Collection:")
        anime_ids = set()  # Using a set to store unique anime IDs
        for media_list in media_list_collection['lists']:
            for entry in media_list.get('entries', []):
                anime_id = entry['media']['id']
                media_title = entry['media']['title']['romaji']
                if anime_id not in anime_ids:  # Check if anime ID has not been printed before
                    anime_ids.add(anime_id)  # Add anime ID to the set
                    print(f"- ID: {anime_id}, Title: {media_title}")

        # Fetch anime info for the collected IDs
        anime_info = fetch_anime_info(anime_ids)
        for info in anime_info:
            print("Title (Romaji):", info["title"]["romaji"])
            print("Title (English):", info["title"]["english"])
            print("Title (Native):", info["title"]["native"])
            print("Episodes:", info["episodes"])
            print("Status:", info["status"])
            print("Average Score:", info["averageScore"])
            print("Genres:", ", ".join(info["genres"]))
            print("Description:", info["description"])
            print("Cover Image:", info["coverImage"]["extraLarge"])
            print("\n")
            
            # Store anime info in JSON file
            format_and_store_info(info, info["episodes"])
else:
    print("AniList access token or user ID not found in the environment variables.")
