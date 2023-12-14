import typing as t
import aiohttp
from bs4 import BeautifulSoup

import db


class Page:
    def __init__(self, name, url, description):
        self.name = name
        self.url = url
        self.description = description


PAGES = [
    Page("explorer", "https://materovcompetition.org/explorer", "the Explorer class specs"),
    Page("pioneer", "https://materovcompetition.org/pioneer", "the Pioneer class specs"),
    Page("ranger", "https://materovcompetition.org/ranger", "the Ranger class specs"),
    Page("navigator", "https://materovcompetition.org/navigator", "the Navigator class specs"),
    Page("scout", "https://materovcompetition.org/scout", "the Scout class specs"),
    Page("scoring", "https://materovcompetition.org/scoring", "scoring rules"),
    Page("worlds", "https://materovcompetition.org/world-championship", "the world championships"),
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
    new_text = soup.find(id="main-content").prettify()

    if not await db.check_for_page(page.url):
        await db.add_page(page.url, new_text)
        return None

    old_text = (await db.get_page_by_url(page.url))["text"]

    if old_text == new_text:
        return None

    await db.update_page(page.url, new_text)

    return old_text, new_text


async def get_all_updates():
    async with aiohttp.ClientSession() as session:
        results = []
        for page in PAGES:
            results.append(await get_page_update(page, session))

    diffs = {
        PAGES[i].name: results[i] for i in range(len(PAGES)) if results[i] is not None
    }

    return diffs
