from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from questdb.ingress import Sender, TimestampNanos
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.oauth import refresh_access_token
from twitchAPI.type import AuthScope
import os
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")

app = FastAPI()

@app.post("/webhook/callback")
async def receive_challenge(request: Request):
    data = await request.json()  # Parse the incoming JSON data
    print("challenge:", data)
    twitch_eventsub_message_type = request.headers.get("Twitch-Eventsub-Message-Type")
    print("Twitch-Eventsub-Message-Type:", twitch_eventsub_message_type)
    if twitch_eventsub_message_type == "webhook_callback_verification":
        return PlainTextResponse(content=data["challenge"], status_code=200)
    else:
        send_to_questdb(data)
        return "webhook recieved"

@app.get("/auth/")
async def get_auth_code(request: Request):
    query_params = request.query_params
    code = query_params.get("code")
    scope = query_params.get("scope")
    state = query_params.get("state")
    await set_refresh_token(code,state,scope)

    return 'Authorization recieved'


async def set_refresh_token(auth_code,state,scope):
    twitch = await Twitch(APP_ID, APP_SECRET)
    auth = UserAuthenticator(twitch, AuthScope.CHANNEL_BOT)
    token, refresh_token = await auth.authenticate(user_token=auth_code)
    conf = 'http::addr=localhost:9000;'
    with Sender.from_conf(conf) as sender:
        sender.row('refresh_tokens',
            symbols={'broadcaster': state,
                'scope':scope},
            columns={'refresh_token': refresh_token},
            at=TimestampNanos.now())





def send_to_questdb(data):
    conf = 'http::addr=localhost:9000;'
    with Sender.from_conf(conf) as sender:
        sender.row('messages',
            symbols={'broadcaster_user_id': data['event']['broadcaster_user_id'],
            'broadcaster_user_name': data['event']['broadcaster_user_name'],
            'chatter_user_id': data['event']['chatter_user_id'],
            'chatter_user_name': data['event']['chatter_user_name'],
            'chatter_user_login': data['event']['chatter_user_login']},
            columns={'message': data['event']['message']['text'],
                'message_id': data['event']['message_id'],
                'color': data['event']['color'],
                'cheer': data['event']['cheer']},
            at=TimestampNanos.now())
