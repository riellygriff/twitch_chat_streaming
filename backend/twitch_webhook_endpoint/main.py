import functions_framework
from flask import make_response
from questdb.ingress import Sender, TimestampNanos

@functions_framework.http
def receive_webhook(request):

    data = request.get_json(silent=True)
    request_args = request.args

    # print("challenge:", data)
    twitch_eventsub_message_type = request.headers.get("Twitch-Eventsub-Message-Type")
    print("Twitch-Eventsub-Message-Type:", twitch_eventsub_message_type)
    if twitch_eventsub_message_type == "webhook_callback_verification":
        return make_response(data['challenge'], 200, {'content_type':'text/plain; charset=utf-8'})
    else:
        # print(data)
        send_to_questdb(data)
        return "webhook recieved"


def send_to_questdb(data):
    conf = 'http::addr=10.128.0.5:9000;username=admin;password=quest;'
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
    print('row inserted')
