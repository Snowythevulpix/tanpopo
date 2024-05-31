import os
import requests
from urllib.parse import urlparse, parse_qs
import webbrowser
from dotenv import load_dotenv
import tkinter as tk
import subprocess

# Load environment variables from .env file
load_dotenv()

# Step 1: Register your application and obtain client credentials
CLIENT_ID = '17593'
CLIENT_SECRET = '5FLMx3yxCAmHqjMCwkb2QTWKqZ2DFBqCOLZxM5iC'
REDIRECT_URI = 'https://ninestails.pagostunes.xyz/auth.html'

# Step 2: Redirect user to AniList's authorization page
def get_authorization_code():
    auth_url = 'https://anilist.co/api/v2/oauth/authorize'
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code'  # Use 'code' for Authorization Code Grant flow
    }
    webbrowser.open_new(auth_url + '?' + '&'.join([f'{key}={value}' for key, value in params.items()]))

# Step 3: Exchange authorization code for access token
def exchange_code_for_token(authorization_code):
    token_url = 'https://anilist.co/api/v2/oauth/token'
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
        'code': authorization_code
    }
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        if access_token:
            # Write data to .env file
            with open('.env', 'w') as f:
                f.write(f"ANILIST_ACCESS_TOKEN={access_token}\n")
                user_info = get_user_info(access_token)
                if user_info:
                    user_id = user_info['id']
                    print("User ID:", user_id)
                    f.write(f"ANILIST_ID={user_id}\n")
                    f.write(f"ANILIST_USERNAME={user_info['name']}\n")
                    f.write(f"ANILIST_AVATAR={user_info['avatar']['large']}\n")
                else:
                    print("Failed to fetch user info.")
            return access_token
        else:
            print("Failed to exchange authorization code for access token.")
            return None
    else:
        print("Failed to exchange authorization code for access token.")
        return None

# Step 4: Fetch user information using access token
def get_user_info(access_token):
    user_info_url = 'https://graphql.anilist.co'
    query = '''
    query {
        Viewer {
            id
            name
            avatar {
                large
            }
        }
    }
    '''
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.post(user_info_url, json={'query': query}, headers=headers)
    if response.status_code == 200:
        return response.json()['data']['Viewer']
    else:
        print("Failed to fetch user info.")
        return None

# Main function
def main():
    # Ensure .env file exists or create it if not
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            pass

    # Step 1: Redirect user to AniList's authorization page
    get_authorization_code()

    # Create a Tkinter window
    root = tk.Tk()
    root.title("Authorization Code")

    # Function to handle button click
    def submit_authorization_code():
        authorization_code = entry.get()
        if authorization_code:
            access_token = exchange_code_for_token(authorization_code)
            if access_token:
                print("Access token:", access_token)
                subprocess.Popen(["python", "tanpopo.py"])

            else:
                print("Authorization failed.")
            root.destroy()
        else:
            print("Please enter the authorization code.")

    # Create a label
    label = tk.Label(root, text="Enter Authorization Code:")
    label.pack()

    # Create an entry widget
    entry = tk.Entry(root)
    entry.pack()

    # Create a submit button
    submit_button = tk.Button(root, text="Submit", command=submit_authorization_code)
    submit_button.pack()

    root.mainloop()

if __name__ == "__main__":
    main()
