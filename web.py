import dataclasses
import typing as t
import aiohttp
from bs4 import BeautifulSoup

import db


MATE_FILTER_ID = "main-content"


@dataclasses.dataclass
class Page:
    name: str
    url: str
    filter_id: str
    description: str


PAGES = [
    Page("explorer", "https://materovcompetition.org/explorer", MATE_FILTER_ID, "the Explorer class specs"),
    Page("pioneer", "https://materovcompetition.org/pioneer", MATE_FILTER_ID, "the Pioneer class specs"),
    Page("ranger", "https://materovcompetition.org/ranger", MATE_FILTER_ID, "the Ranger class specs"),
    Page("navigator", "https://materovcompetition.org/navigator", MATE_FILTER_ID, "the Navigator class specs"),
    Page("scout", "https://materovcompetition.org/scout", MATE_FILTER_ID, "the Scout class specs"),
    Page("scoring", "https://materovcompetition.org/scoring", MATE_FILTER_ID, "scoring rules"),
    Page("worlds", "https://materovcompetition.org/world-championship", MATE_FILTER_ID, "the world championships"),
    Page("rulings", "https://docs.google.com/document/d/e/2PACX-1vS-i5t8yrwIYMjHzpS6sSYyuG8_quCGhyDMnxPqG2eDmI6QacK08fTVS2_VQF-d1vfjA7ydJgbu4itI/pub", "contents", "official rulings"),
    # Page("debug", "https://c.xkcd.com/random/comic/", "comic", "debug page"),
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
    new_text = soup.find(id=page.filter_id).prettify()

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
