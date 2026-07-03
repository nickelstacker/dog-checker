"""HTTP helpers shared by the scrapers."""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

TIMEOUT = 30


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    return s


def get_soup(session: requests.Session, url: str, **kwargs) -> BeautifulSoup:
    r = session.get(url, timeout=TIMEOUT, **kwargs)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")
