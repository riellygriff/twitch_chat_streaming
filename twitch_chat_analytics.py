import marimo

__generated_with = "0.9.17"
app = marimo.App(width="medium")


@app.cell
def __(mo):
    mo.md(
        r"""
        # <u>**Twitch Chat Analytics**</u>
        Check out some analytics of chat from your favorite streamer. From things that what user has chatted the most in the last hour to how many times a message has been spammed it can all be found right here.
        """
    )
    return


@app.cell
def __(pg):
    _conn_str = 'user=admin password=quest host=127.0.0.1 port=8812 dbname=qdb'

    with pg.connect(_conn_str, autocommit=True) as _connection:
        with _connection.cursor() as _cur:
            _query = f'''
            select distinct broadcaster
            from refresh_tokens
            '''
            _cur.execute(_query)
            _records = _cur.fetchall()
            streamers = [_record[0] for _record in _records]
    # streamers
    return (streamers,)


@app.cell
def __(mo, streamers):
    refresh = mo.ui.refresh(default_interval=10)
    streamer = mo.ui.dropdown(options=streamers,label='Streamer',value='wafflesmacker')
    mo.vstack([mo.md('Select the streamer you would like to see the chat for'),
    mo.hstack([streamer,refresh])])
    return refresh, streamer


@app.cell
def __(pg, pl, refresh, streamer):
    _conn_str = 'user=admin password=quest host=127.0.0.1 port=8812 dbname=qdb'
    _columns = ['broadcaster','chatter','message','message_id','color','timestamp']
    refresh
    with pg.connect(_conn_str, autocommit=True) as _connection:
        with _connection.cursor() as _cur:
            _query = f'''
            select broadcaster_user_name,chatter_user_name,message,message_id,color,timestamp
            from messages
            where lower(broadcaster_user_name) = '{streamer.value.lower()}'
            '''
            _cur.execute(_query)
            _records = _cur.fetchall()
            df = pl.DataFrame(_records,orient='row',schema=_columns)
            df = df.with_columns(pl.col('timestamp').dt.convert_time_zone(time_zone='UTC'))
    # df
    return (df,)


@app.cell
def __(mo):
    mo.md(
        r"""
        ''
        ## <u>**Top Chatters**</u>
        See who has sent the most messages in chat over the last hours
        """
    )
    return


@app.cell
def __(mo):
    timeframe1 = mo.ui.slider(start=1,stop=12,show_value=True,debounce=True)
    mo.vstack([mo.md(f'How many previous hours to show'),timeframe1],align='start')
    return (timeframe1,)


@app.cell
def __(alt, datetime, df, mo, pl, timeframe1, timezone):
    _df = df.filter(pl.col('timestamp').dt.offset_by(f'{timeframe1.value}h')>datetime.now(timezone.utc))
    _df = _df.group_by('chatter').agg(pl.col('message_id').len().alias('chats'))
    _df = _df.sort(by='chats',descending=True)
    _chart = _df.plot.bar(x='chats',y=alt.Y('chatter').sort('-x'),color = 'chatter')
    _chart = mo.ui.altair_chart(_chart)
    _chart
    return


@app.cell
def __(mo):
    mo.md(
        r"""
        ''
        ## <u>**Number of Chats over time**</u>
        """
    )
    return


@app.cell
def __(mo):
    timeframe2 = mo.ui.slider(start=1,stop=12,show_value=True,debounce=True)
    increment = mo.ui.slider(start=1,stop=60,show_value=True,debounce=True,value=5)
    mo.hstack([
    mo.vstack([mo.md(f'How many previous hours to show'),timeframe2],align='center'),
    mo.vstack([mo.md(f'Minute Increment'),increment],align='center')
    ],justify='start')
    return increment, timeframe2


@app.cell
def __(datetime, df, increment, mo, pl, timeframe2, timezone):
    _df = df.filter(pl.col('timestamp').dt.offset_by(f'{timeframe2.value}h')>datetime.now(timezone.utc))
    _df = _df.with_columns(pl.col('timestamp').dt.truncate(f'{increment.value}m'))
    _df = _df.group_by('timestamp').agg(pl.col('message_id').len().alias('chats'))
    _chart = _df.plot.line(x='timestamp',y = 'chats')
    _chart = mo.ui.altair_chart(_chart)
    _chart
    return


@app.cell
def __(mo):
    mo.md(
        r"""
        ''
        ## <u>**Specific Chat Message**</u>
        Search for a specific message in chat to see how many time it has appeared and who has said it the most.
        """
    )
    return


@app.cell
def __(mo):
    chat_message = mo.ui.text(placeholder='Search...',label='Message')
    timeframe3 = mo.ui.slider(start=1,stop=12,show_value=True,debounce=True)
    mo.hstack([
    mo.vstack([mo.md(f'How many previous hours to show'),timeframe3],align='center'),
    mo.vstack([mo.md(f'Chat to find'),chat_message],align='center')
    ],justify='start')
    return chat_message, timeframe3


@app.cell
def __(alt, chat_message, datetime, df, mo, pl, timeframe3, timezone):
    _df = (df.filter(pl.col('timestamp').dt.offset_by(f'{timeframe3.value}h')>datetime.now(timezone.utc))
          .filter(pl.col('message').str.to_lowercase().str.contains(chat_message.value.lower()))
            )
    _total_count = _df.height
    _df = _df.group_by('chatter').agg(pl.col('message_id').len().alias('chats'))
    _df = _df.sort(by='chats',descending=True)
    _chart = _df.plot.bar(x='chats',y=alt.Y('chatter').sort('-x'),color = 'chatter')
    _chart = mo.ui.altair_chart(_chart)
    mo.vstack([mo.md(f'''**{chat_message.value.lower()}**
    has appeared in chat 
    **{_total_count}**
    times in the last {timeframe3.value} hours'''),_chart])
    return


@app.cell
def __():
    import marimo as mo
    import psycopg as pg
    import polars as pl
    from datetime import datetime, timedelta, timezone
    import altair as alt
    return alt, datetime, mo, pg, pl, timedelta, timezone


if __name__ == "__main__":
    app.run()
