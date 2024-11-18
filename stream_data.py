import os
from dotenv import load_dotenv
from questdb.ingress import Sender, TimestampNanos
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.oauth import refresh_access_token
from twitchAPI.type import AuthScope
from twitchAPI.eventsub.webhook import EventSubWebhook
from twitchAPI.object.eventsub import ChannelChatMessageEvent
import asyncio
import psycopg as pg

load_dotenv()

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
TARGET_SCOPES = [
    AuthScope.USER_READ_CHAT,
    AuthScope.USER_BOT,
    AuthScope.CHANNEL_BOT
]
EVENTSUB_URL = "https://loving-moth-famous.ngrok-free.app/webhook"
TARGET_USERNAME = "rigriff2"
broadcaster = "wafflesmacker"


async def on_follow(data: ChannelChatMessageEvent):
    # our event happened, lets do things with the data we got!
    print(data.event)
    print(f"{data.event.user_name} now follows {data.event.broadcaster_user_name}!")


async def eventsub_webhook_example():
    # try:
    # create the api instance and get the ID of the target user
    twitch = await Twitch(APP_ID, APP_SECRET)
    user = await first(twitch.get_users(logins=TARGET_USERNAME))
    broadcast = await first(twitch.get_users(logins=broadcaster))

    # the user has to authenticate once using the bot with our intended scope.
    # since we do not need the resulting token after this authentication, we just discard the result we get from authenticate()
    # Please read up the UserAuthenticator documentation to get a full view of how this process works
    auth = UserAuthenticator(twitch, TARGET_SCOPES)
    await auth.authenticate()

    token, refresh = await update_access_token(broadcaster)
    await twitch.set_user_authentication(token=token,scope = [AuthScope.CHANNEL_BOT],refresh_token = refresh)

    # basic setup, will run on port 8080 and a reverse proxy takes care of the https and certificate
    print("setting up eventsub client...")
    eventsub = EventSubWebhook(EVENTSUB_URL, 8082, twitch)
    eventsub.secret = "your secret goes here"
    eventsub.wait_for_subscription_confirm = False
    print("eventsub client setup")
    # unsubscribe from all old events that might still be there
    # this will ensure we have a clean slate
    print("unsubscribing from old events...")
    await eventsub.unsubscribe_all()
    print("old events unsubscribed")
    # start the eventsub client
    print("starting eventsub client...")
    eventsub.start()
    print("eventsub client started")
    # subscribing to the desired eventsub hook for our user
    # the given function (in this example on_follow) will be called every time this event is triggered
    # the broadcaster is a moderator in their own channel by default so specifying both as the same works in this example
    await eventsub.listen_channel_chat_message(broadcast.id, user.id, on_follow)
    await eventsub.listen_channel_chat_message(user.id, user.id, on_follow)

    # eventsub will run in its own process
    # so lets just wait for user input before shutting it all down again
    try:
        input("press Enter to shut down...")
    finally:
        # stopping both eventsub as well as gracefully closing the connection to the API
        await eventsub.stop()
        await twitch.close()
    print("done")


def get_recent_refresh(broadcaster):
    conn_str = 'user=admin password=quest host=127.0.0.1 port=8812 dbname=qdb'
    with pg.connect(conn_str, autocommit=True) as connection:
        with connection.cursor() as cur:
            query = f'''
            select scope,
            refresh_token
            from refresh_tokens
            where broadcaster = '{broadcaster}'
            and timestamp = (select max(timestamp) from refresh_tokens where broadcaster = '{broadcaster}')
            '''
            cur.execute(query)
            records = cur.fetchall()[0]
            scope = records[0]
            token = records[1]
            return scope, token


async def update_access_token(broadcaster):
    scope, token = get_recent_refresh(broadcaster)
    access, refresh = await refresh_access_token(refresh_token = token,app_id = APP_ID,app_secret = APP_SECRET)
    conf = 'http::addr=localhost:9000;'
    with Sender.from_conf(conf) as sender:
        sender.row('refresh_tokens',
            symbols={'broadcaster': broadcaster,
                'scope':scope},
            columns={'refresh_token': refresh},
            at=TimestampNanos.now())
    return access, refresh
# lets run our example
asyncio.run(eventsub_webhook_example())
