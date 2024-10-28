import discord
from discord import app_commands
from discord.ext import tasks
import io
import itertools
import json
import ghdiff
import imgkit
import logging
import difflib
import db
import web
from web import PAGES, PAGES_BY_NAME

logging.basicConfig(filename="bot.log", encoding="utf-8", level=logging.DEBUG,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger().addHandler(logging.StreamHandler())

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

test_guild = discord.Object(id=833577630997413980)

subscribe_group = app_commands.Group(name="subscribe", description="Subscribe to updates to the MATE website")
unsubscribe_group = app_commands.Group(name="unsubscribe", description="Unsubscribe from updates")

for page in PAGES:
    name = page.name


    @subscribe_group.command(
        name=name,
        description=f"Subscribe to updates about {page.description}",
    )
    async def subcommand(interaction: discord.Interaction, channel: discord.TextChannel = None) -> None:
        subcommand_name = interaction.command.name
        guild_id = int(interaction.guild_id)
        channel_id = int(interaction.channel_id) if channel is None else int(channel.id)

        if not await db.check_for_subscription(channel_id, subcommand_name):
            await db.add_subscription(guild_id, channel_id, subcommand_name)
            await interaction.response.send_message(
                f"Subscribed <#{channel_id}> to updates about {PAGES_BY_NAME[subcommand_name].description}")
        else:
            await interaction.response.send_message(f"<#{channel_id}> is already subscribed to {subcommand_name}")


    @unsubscribe_group.command(
        name=name,
        description=f"Unsubscribe from updates about {page.description}"
    )
    async def subcommand(interaction: discord.Interaction, channel: discord.TextChannel = None) -> None:
        subcommand_name = interaction.command.name
        channel_id = int(interaction.channel_id) if channel is None else int(channel.id)

        if await db.check_for_subscription(channel_id, subcommand_name):
            await db.remove_subscription(channel_id, subcommand_name)
            await interaction.response.send_message(f"Unsubscribed <#{channel_id}> from {subcommand_name} updates")
        else:
            await interaction.response.send_message(f"<#{channel_id}> is not subscribed to {subcommand_name}")


@unsubscribe_group.command(name="all", description="Unsubscribe from all updates in all channels")
async def unsubscribe_all(interaction: discord.Interaction):
    await db.remove_all_guild_subscriptions(int(interaction.guild_id))
    await interaction.response.send_message(f"Unsubscribed all channels from all topics")


tree.add_command(subscribe_group)
tree.add_command(unsubscribe_group)


@tree.command(
    name="list",
    description="List subscriptions",
)
async def list_cmd(interaction: discord.Interaction):
    subscriptions = await db.get_subscriptions_for_guild(int(interaction.guild_id))

    if len(subscriptions) == 0:
        await interaction.response.send_message("This server has no subscriptions")
        return

    subscriptions_dict = {g[0]: list(g[1]) for g in itertools.groupby(subscriptions, lambda s: s["channel_id"])}

    embed = discord.Embed()
    embed.add_field(
        name="Server subscriptions",
        value="\n\n".join(
            [f"<#{channel_id}>\n" + "\n".join(
                ["\u200b \u200b \u200b \u200b " + s["topic"] for s in channel_subscriptions])
             for channel_id, channel_subscriptions in subscriptions_dict.items()]
        )
    )

    await interaction.response.send_message(embed=embed)


@tree.command(
    name="fetch",
    description="Manually fetch updates",
    guild=test_guild,
)
async def fetch(interaction: discord.Interaction):
    await interaction.response.send_message("Fetching updates")
    await fetch_updates()


async def publish_embed(page_name: str, embed: discord.Embed, img=None):
    if img is not None:
        embed.set_image(url="attachment://diff.png")

    for subscription in await db.get_subscriptions_for_topic(page_name):
        try:
            if img is not None:
                await client.get_channel(subscription["channel_id"]).send(
                    embed=embed,
                    file=discord.File(io.BytesIO(img), filename="diff.png")
                )
            else:
                await client.get_channel(subscription["channel_id"]).send(
                    embed=embed,
                )
        except (discord.HTTPException, discord.Forbidden, ValueError) as e:
            logging.error(f"Failed to send message to {subscription['channel_id']}: {type(e)}")


async def fetch_updates():
    logging.debug("Fetching updates")
    doc_pairs = await web.get_all_updates()

    for page_name, result in doc_pairs.items():
        logging.info(f"Page '{page_name}' has been updated")
        page = PAGES_BY_NAME[page_name]
        old_text, new_text, new_page_soup = result

        # If new links have been added, link them directly in the notification
        links = new_page_soup.find_all("a")
        new_links = []
        for link in links:
            href = link.get("href")
            if href is not None and "http" in href and href not in old_text and link.get_text():
                new_links.append(link)

        if len(new_links) > 0:
            embed = discord.Embed(title=f"The {page_name} page on the MATE website has been updated!")
            field_text = ""
            for link in new_links:
                field_text += f"[{link.get_text()}]({link.get('href')})\n"
            embed.add_field(name="New links have been added", value=field_text, inline=False)
            embed.add_field(name="Check out the updated page", value=page.url, inline=False)

            await publish_embed(page_name, embed)
            return

        diff = difflib.ndiff(old_text.splitlines(), new_text.splitlines())

        change_count = 0
        for line in diff:
            if line.startswith("+") or line.startswith("-"):
                change_count += 1

        if change_count < 10:
            # Otherwise, if the diff is short enough, include an image of the diff
            diff_html = ghdiff.diff(old_text, new_text)

            # imgkit.config(wkhtmltoimage='wkhtmltoimage.exe')
            img = imgkit.from_string(diff_html, False)

            embed = discord.Embed(title=f"The {page_name} page on the MATE website has been updated!")
            embed.add_field(name="Check out the updated page", value=page.url)
            await publish_embed(page_name, embed, img)

        # Otherwise, simply provide the full diff as an attachment
        embed = discord.Embed(title=f"The {page_name} page on the MATE website has been updated!")
        embed.add_field(name="Many lines were changed, but no links were added", value=page.url)
        await publish_embed(page_name, embed)


@tasks.loop(seconds=300)
async def fetch_loop():
    try:
        await fetch_updates()
    except Exception as e:
        logging.exception(e)


@fetch_loop.before_loop
async def before_fetch_loop():
    await client.wait_until_ready()


@tree.command(name='sync', description='Owner only', guild=test_guild)
async def sync(interaction: discord.Interaction):
    if interaction.user.id == 306244074984177664:
        await tree.sync()
        logging.info('Command tree synced.')
    else:
        await interaction.response.send_message('You must be the developer to use this command!')


@client.event
async def on_ready():
    fetch_loop.start()
    # await tree.sync()
    logging.info("Connected to Discord")


with open("secrets.json") as f:
    secret = json.load(f)
    client.run(secret["TOKEN"])
