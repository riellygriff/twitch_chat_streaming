from questdb.ingress import Sender, TimestampNanos
import requests
import os
from dotenv import load_dotenv
import polars as pl
import psycopg as pg
import streamlit as st

data = {
    "subscription": {
        "id": "4db4650e-bcb6-4ce7-bb3e-e0b882479ac3",
        "status": "enabled",
        "type": "channel.chat.message",
        "version": "1",
        "condition": {"broadcaster_user_id": "566671230", "user_id": "566671230"},
        "transport": {
            "method": "webhook",
            "callback": "https://535c-104-167-233-203.ngrok-free.app/webhook/callback",
        },
        "created_at": "2024-11-07T01:15:34.592713882Z",
        "cost": 0,
    },
    "event": {
        "broadcaster_user_id": "566671230",
        "broadcaster_user_login": "rigriff2",
        "broadcaster_user_name": "RiGriff2",
        "source_broadcaster_user_id": None,
        "source_broadcaster_user_login": None,
        "source_broadcaster_user_name": None,
        "chatter_user_id": "566671230",
        "chatter_user_login": "rigriff2",
        "chatter_user_name": "RiGriff2",
        "message_id": "6f91040c-1c2c-4c3f-9c64-14a96ddf5355",
        "source_message_id": None,
        "message": {
            "text": "hi",
            "fragments": [
                {
                    "type": "text",
                    "text": "hi",
                    "cheermote": None,
                    "emote": None,
                    "mention": None,
                }
            ],
        },
        "color": "#DAA520",
        "badges": [
            {"set_id": "broadcaster", "id": "1", "info": ""},
            {"set_id": "premium", "id": "1", "info": ""},
        ],
        "source_badges": None,
        "message_type": "text",
        "cheer": None,
        "reply": None,
        "channel_points_custom_reward_id": None,
        "channel_points_animation_id": None,
    },
}

# conf = 'http::addr=localhost:9000;'
# with Sender.from_conf(conf) as sender:
#     sender.row('messages',
#         symbols={'broadcaster_user_id': data['event']['broadcaster_user_id'],
#         'broadcaster_user_name': data['event']['broadcaster_user_name'],
#         'chatter_user_id': data['event']['chatter_user_id'],
#         'chatter_user_name': data['event']['chatter_user_name'],
#         'chatter_user_login': data['event']['chatter_user_login']},
#         columns={'message': data['event']['message']['text'],
#             'message_id': data['event']['message_id'],
#             'color': data['event']['color'],
#             # 'badges': data['event']['badges'],
#             'cheer': data['event']['cheer']},
#         at=TimestampNanos.now())


# load_dotenv()

# APP_ID = os.getenv("APP_ID")
# APP_SECRET = os.getenv("APP_SECRET")
# url = 'https://id.twitch.tv/oauth2/token'
# body = { 'client_id':APP_ID,
# 'client_secret':APP_SECRET,
# 'grant_type':'authorization_code',
# 'code': 'hoxhh0qn997giurzi65pa070dtlymr',
# 'redirect_uri': 'http://localhost:17563'}
# headers = {'Content-Type': 'application/x-www-form-urlencoded'}
# response = requests.post(url, data=body, headers=headers)
# print(response.text)


# https://id.twitch.tv/oauth2/authorize
#     ?response_type=code
#     &client_id=xrk9xqkcj01qet2hwv50oziq4vqdpw
#     &redirect_uri=https://loving-moth-famous.ngrok-free.app/auth
#     &scope=channel%3Abot
#     &state=crossover_248

# uri = 'postgresql://admin:quest@localhost:8812'
# df = pl.read_database_uri(uri=uri,query='select * from messages')
# print(df)
