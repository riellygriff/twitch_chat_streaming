import functions_framework
from google.cloud import secretmanager
import requests

@functions_framework.http
def start_eventsub(request):
    broadcaster = request.args.get('state')
    user = 'rigriff2'
    app_id, app_secret = get_secrets()
    app_token = get_app_token(app_id, app_secret)
    user_id = get_user_id(user,app_token,app_id)
    broadcaster_id = get_user_id(broadcaster,app_token,app_id)
    eventsub_url = f'https://us-central1-rare-mender-353319.cloudfunctions.net/twitch_webhook'
    if check_existing_eventsubs(app_id, app_token,broadcaster_id):
        return 'Already subscribed'
    else:
        response = listen_for_chats(app_id, app_token,broadcaster_id,user_id,eventsub_url)
    if response == 202:
        return 'Chats will now show up'
    return 'Something went wrong'



def get_secrets():
    client = secretmanager.SecretManagerServiceClient()
    app_name = 'projects/rare-mender-353319/secrets/twitch-app-id-secret/versions/2'
    secret_name = 'projects/rare-mender-353319/secrets/twitch-app-id-secret/versions/1'
    app_id = client.access_secret_version(name=app_name).payload.data.decode('UTF-8')
    app_secret = client.access_secret_version(name=secret_name).payload.data.decode('UTF-8')
    return app_id, app_secret

def get_app_token(app_id, app_secret):
    auth_url = 'https://id.twitch.tv/oauth2/token'
    payload = {
        'client_id': app_id,
        'client_secret': app_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(auth_url, data=payload)
    token = response.json()['access_token']
    return token

def get_user_id(user,app_token,app_id):
    url = f'https://api.twitch.tv/helix/users?login={user}'
    headers = {
        'Client-ID': app_id,
        'Authorization': f'Bearer {app_token}',
        'Content-Type': 'application/json'}
    response = requests.get(url, headers=headers)
    return response.json()['data'][0]['id']

def listen_for_chats(app_id, app_token,broadcaster_id,chatter_id,eventsub_url):
    url = 'https://api.twitch.tv/helix/eventsub/subscriptions'
    headers = {
        'Client-ID': app_id,
        'Authorization': f'Bearer {app_token}',
        'Content-Type': 'application/json'}
    payload = {
        'type': 'channel.chat.message',
        'version': '1',
        'condition': {
            'broadcaster_user_id': broadcaster_id,
            'user_id': chatter_id
        },
        'transport': {
            'method': 'webhook',
            'callback': eventsub_url,
            'secret': 'shhhhh its a secret'
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print(response.status_code)
    return response.status_code

def check_existing_eventsubs(app_id, app_token,broadcaster_id):
    url = 'https://api.twitch.tv/helix/eventsub/subscriptions'
    headers = {
        'Client-ID': app_id,
        'Authorization': f'Bearer {app_token}',
        'Content-Type': 'application/json'}
    response = requests.get(url, headers=headers)
    subs = response.json()['data']
    for sub in subs:
        if sub['status'] == 'enabled' and sub['condition']['broadcaster_user_id'] == broadcaster_id:
            return True
    return False
