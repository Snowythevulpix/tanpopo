import requests
import webbrowser
from sub.user_info import *

CLIENT_ID = '17593'
CLIENT_SECRET = '5FLMx3yxCAmHqjMCwkb2QTWKqZ2DFBqCOLZxM5iC'
REDIRECT_URI = 'https://ninestails.xyz/auth.html'


def get_authorization_code():
    auth_url = 'https://anilist.co/api/v2/oauth/authorize'
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code'  # Use 'code' for Authorization Code Grant flow
    }
    webbrowser.open_new(auth_url + '?' + '&'.join([f'{key}={value}' for key, value in params.items()]))


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
