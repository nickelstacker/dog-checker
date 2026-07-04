"""HTTP helpers shared by the scrapers."""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

TIMEOUT = 30

# A full browser-like header set. Some shelter CDNs (e.g. MSPCA) reject requests
# from datacenter IPs like GitHub's runners with a 415/403 unless the request
# looks like a real navigation. These headers get us past that.
BROWSER_HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Connection": "keep-alive",
}


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(BROWSER_HEADERS)
    return s


def get_soup(session: requests.Session, url: str, **kwargs) -> BeautifulSoup:
    r = session.get(url, timeout=TIMEOUT, **kwargs)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")
