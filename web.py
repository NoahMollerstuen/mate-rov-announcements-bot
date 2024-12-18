import dataclasses
import enum
import typing as t
import aiohttp
from bs4 import BeautifulSoup
import logging
import traceback

import db

MATE_FILTER_ID = "main-content"

REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
}


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
    parse_options: ParseOptions = dataclasses.field(
        default_factory=lambda: ParseOptions(MATE_FILTER_ID, ParseType.FULL_HTML))


PAGES = [
    Page("explorer", "https://materovcompetition.org/explorer", "the Explorer class specs"),
    Page("pioneer", "https://materovcompetition.org/pioneer", "the Pioneer class specs"),
    Page("ranger", "https://materovcompetition.org/ranger", "the Ranger class specs"),
    Page("navigator", "https://materovcompetition.org/navigator", "the Navigator class specs"),
    Page("scout", "https://materovcompetition.org/scout", "the Scout class specs"),
    Page("scoring", "https://materovcompetition.org/scoring", "scoring rules"),
    Page("worlds", "https://materovcompetition.org/world-championship", "the world championships"),
    Page("rulings",
         "https://docs.google.com/document/d/e/2PACX-1vS-i5t8yrwIYMjHzpS6sSYyuG8_quCGhyDMnxPqG2eDmI6QacK08fTVS2_VQF-d1vfjA7ydJgbu4itI/pub",
         "official rulings", ParseOptions("contents", ParseType.TEXT_ONLY)),
]

PAGES_BY_NAME = {
    page.name: page for page in PAGES
}


async def get_page_update(page: Page, session: aiohttp.ClientSession) -> t.Optional[t.Tuple[str, str, BeautifulSoup]]:
    try:
        async with session.get(page.url, headers=REQUEST_HEADERS) as resp:
            new_text_raw = await resp.text()
    except aiohttp.ClientConnectorError:
        logging.warning(f"Failed to fetch page {page.name} at {page.url}")
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

    return old_text, new_text, soup


async def get_all_updates() -> dict[str, tuple[str, str, BeautifulSoup]]:
    async with aiohttp.ClientSession() as session:
        results = []
        for page in PAGES:
            try:
                results.append(await get_page_update(page, session))
            except Exception as e:
                results.append(None)
                logging.error(f"Error fetching page {page.name} at {page.url}:\n\n" + traceback.format_exc())

    diffs = {
        PAGES[i].name: results[i] for i in range(len(PAGES)) if results[i] is not None
    }

    return diffs
