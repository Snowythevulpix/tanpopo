import requests


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
