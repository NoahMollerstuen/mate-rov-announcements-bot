import dataclasses
import enum
import typing as t
import aiohttp
from bs4 import BeautifulSoup

import db


MATE_FILTER_ID = "main-content"


class ParseType(enum.Enum):
    FULL_HTML = ("html", lambda s: s.prettify())
    TEXT_ONLY = ("text", lambda s: s.get_text("\n"))

    def __new__(cls, value, parse_func):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.parse_func = parse_func
        return obj


@dataclasses.dataclass
class ParseOptions:
    filter_id: t.Optional[str]
    parse_type: ParseType


@dataclasses.dataclass
class Page:
    name: str
    url: str
    description: str
    parse_options: ParseOptions = ParseOptions(MATE_FILTER_ID, ParseType.FULL_HTML)


PAGES = [
    Page("explorer", "https://materovcompetition.org/explorer", "the Explorer class specs"),
    Page("pioneer", "https://materovcompetition.org/pioneer", "the Pioneer class specs"),
    Page("ranger", "https://materovcompetition.org/ranger", "the Ranger class specs"),
    Page("navigator", "https://materovcompetition.org/navigator", "the Navigator class specs"),
    Page("scout", "https://materovcompetition.org/scout", "the Scout class specs"),
    Page("scoring", "https://materovcompetition.org/scoring", "scoring rules"),
    Page("worlds", "https://materovcompetition.org/world-championship", "the world championships"),
    Page("rulings", "https://docs.google.com/document/d/e/2PACX-1vS-i5t8yrwIYMjHzpS6sSYyuG8_quCGhyDMnxPqG2eDmI6QacK08fTVS2_VQF-d1vfjA7ydJgbu4itI/pub",
         "official rulings", ParseOptions("contents", ParseType.TEXT_ONLY)),
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
    if page.parse_options.filter_id is not None:
        soup = soup.find(id=page.parse_options.filter_id)
    new_text = page.parse_options.parse_type.parse_func(soup)

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
