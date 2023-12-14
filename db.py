from tinydb import Query
from aiotinydb import AIOTinyDB

DB_PATH = "db.json"

db = AIOTinyDB(DB_PATH)


def get_subscriptions(db: AIOTinyDB):
    return db.table('subscriptions')


def get_pages(db: AIOTinyDB):
    return db.table('pages')


query = Query()


async def add_subscription(guild_id: int, channel_id: int, topic: str):
    print(f"Adding subscription {guild_id}, {channel_id}, {topic}")
    async with AIOTinyDB(DB_PATH) as db:
        get_subscriptions(db).insert({"guild_id": guild_id, "channel_id": channel_id, "topic": topic})


async def remove_subscription(channel_id: int, topic: str):
    async with db:
        get_subscriptions(db).remove((query.channel_id == channel_id) & (query.topic == topic))


async def remove_all_guild_subscriptions(guild_id: int):
    async with db:
        get_subscriptions(db).remove(query.guild_id == guild_id)


async def get_subscriptions_for_topic(topic: str):
    async with db:
        return get_subscriptions(db).search(query.topic == topic)


async def get_subscriptions_for_guild(guild_id: int):
    async with db:
        return get_subscriptions(db).search(query.guild_id == guild_id)


async def check_for_subscription(channel_id: int, topic: str):
    async with db:
        return get_subscriptions(db).contains((query.channel_id == channel_id) & (query.topic == topic))


async def add_page(url: str, text: str):
    async with db:
        get_pages(db).insert({"url": url, "text": text})


async def update_page(url: str, text: str):
    async with db:
        get_pages(db).update({"text": text}, query.url == url)


async def check_for_page(url: str):
    async with db:
        return get_pages(db).contains(query.url == url)


async def get_page_by_url(url: str):
    async with db:
        return get_pages(db).get(query.url == url)
