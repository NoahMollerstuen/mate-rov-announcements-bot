import typing as t
import asyncio
import aiohttp
from bs4 import BeautifulSoup

import db


class Page:
    def __init__(self, name, url, description):
        self.name = name
        self.url = url
        self.description = description


PAGES = [
    Page("explorer", "https://materovcompetition.org/explorerspecs", "the Explorer class specs"),
    Page("pioneer", "https://materovcompetition.org/pioneerspecs", "the Pioneer class specs"),
    Page("ranger", "https://materovcompetition.org/rangerspecs", "the Ranger class specs"),
    Page("navigator", "https://materovcompetition.org/navigatorspecs", "the Navigator class specs"),
    Page("scout", "https://materovcompetition.org/scoutspecs", "the Scout class specs"),
    Page("scoring", "https://materovcompetition.org/scoring", "scoring rules"),
    Page("worlds", "https://materovcompetition.org/worldchampinfo", "the world championships"),
]

PAGES_BY_NAME = {
    page.name: page for page in PAGES
}


async def get_page_update(page: Page, session: aiohttp.ClientSession) -> t.Optional[t.Tuple[str, str]]:
    try:
        async with session.get(page.url) as resp:
            new_text_raw = await resp.text()
    except aiohttp.ClientConnectorError:
        return None

    soup = BeautifulSoup(new_text_raw, 'html.parser')
    new_text = soup.find(id="content").prettify()

    if not db.check_for_page(page.url):
        db.add_page(page.url, new_text)
        return None

    old_text = db.get_page_by_url(page.url)["text"]

    if old_text == new_text:
        return None

    db.update_page(page.url, new_text)

    return old_text, new_text


async def get_all_updates():

    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*(get_page_update(page, session) for page in PAGES))

    diffs = {
        PAGES[i].name: results[i] for i in range(len(PAGES)) if results[i] is not None
    }

    return diffs
