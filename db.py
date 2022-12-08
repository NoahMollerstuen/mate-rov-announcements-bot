import tinydb.database
from tinydb import Query
from aiotinydb import AIOTinyDB

db = AIOTinyDB('db.json')

subscriptions: tinydb.database.Table
pages: tinydb.database.Table


async def init():
    global subscriptions, pages
    await db.__aenter__()

    subscriptions = db.table('subscriptions')
    pages = db.table('pages')


async def shutdown():
    await db.__aexit__(None, None, None)

query = Query()


def add_subscription(guild_id: int, channel_id: int, topic: str):
    subscriptions.insert({"guild_id": guild_id, "channel_id": channel_id, "topic": topic})


def remove_subscription(channel_id: int, topic: str):
    subscriptions.remove((query.channel_id == channel_id) & (query.topic == topic))


def remove_all_guild_subscriptions(guild_id: int):
    subscriptions.remove(query.guild_id == guild_id)


def get_subscriptions_for_topic(topic: str):
    return subscriptions.search(query.topic == topic)


def get_subscriptions_for_guild(guild_id: int):
    return subscriptions.search(query.guild_id == guild_id)


def check_for_subscription(channel_id: int, topic: str):
    return subscriptions.contains((query.channel_id == channel_id) & (query.topic == topic))


def add_page(url: str, text: str):
    pages.insert({"url": url, "text": text})


def update_page(url: str, text: str):
    pages.update({"text": text}, query.url == url)


def check_for_page(url: str):
    return pages.contains(query.url == url)


def get_page_by_url(url: str):
    return pages.get(query.url == url)
