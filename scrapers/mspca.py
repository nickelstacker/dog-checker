"""MSPCA (Boston / Nevins Farm / Cape Cod / Northeast).

The adoption search is a WordPress plugin that loads results over AJAX:

    POST /wp-admin/admin-ajax.php
        action=mspca_filter_pets
        nonce=<scraped fresh from the search page each run>
        species=Dog
        paged=<1..max_pages>

Each returned card has a name, age, location and a link to a detail page.
The listing has no weight, so `enrich()` fetches the detail page where the
exact weight lives (e.g. "4.41 lbs").
"""

from __future__ import annotations

import json
import random
import re
import time

import requests
from bs4 import BeautifulSoup

from models import Pet
from util import TIMEOUT

SOURCE = "MSPCA"
SEARCH_PAGE = "https://www.mspca.org/adoption-search/"
AJAX = "https://www.mspca.org/wp-admin/admin-ajax.php"


def _get_nonce(session: requests.Session) -> str:
    """Fetch the search page and pull out the AJAX nonce.

    The site runs LiteSpeed page-cache, which occasionally serves a cached
    variant missing the localized nonce script. A cache-busting query param
    forces a fresh render, and we retry a few times to ride out flakiness.
    """
    last = "unknown"
    for attempt in range(4):
        # No param on the first try (use the warm cache); bust it on retries.
        params = {"_nc": int(time.time() * 1000)} if attempt else None
        try:
            r = session.get(SEARCH_PAGE, timeout=TIMEOUT, params=params)
            if r.status_code == 200:
                m = re.search(r'"nonce":"([a-z0-9]+)"', r.text, re.I)
                if m:
                    return m.group(1)
                cookies = re.findall(r"document\.cookie\s*=\s*[\"']([^\"']+)", r.text)
                setck = dict(r.cookies)
                scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)', r.text)
                last = (f"200 no-nonce bytes={len(r.text)} "
                        f"js_cookies={cookies} resp_cookies={list(setck)} "
                        f"scripts={scripts[:4]} raw={r.text[:900]!r}")
            else:
                last = f"status={r.status_code}"
        except requests.RequestException as exc:
            last = str(exc)
        time.sleep(1.5)
    raise RuntimeError(f"MSPCA: could not get AJAX nonce after 4 tries ({last})")


def _bg_image(style: str) -> str:
    m = re.search(r"url\(['\"]?(.*?)['\"]?\)", style or "")
    return m.group(1) if m else ""


def scrape(session: requests.Session) -> list[Pet]:
    nonce = _get_nonce(session)
    # The plugin randomises result order per request; without a *fixed* seed
    # across page requests the pages overlap and some dogs never appear.
    seed = random.randint(1, 10_000_000)
    pets: list[Pet] = []
    page, max_pages = 1, 1

    while page <= max_pages:
        r = session.post(AJAX, timeout=TIMEOUT, headers={
            "X-Requested-With": "XMLHttpRequest",
            "Referer": SEARCH_PAGE,
        }, data={
            "action": "mspca_filter_pets",
            "nonce": nonce,
            "animal": "Dog",
            "paged": page,
            "random_seed": seed,
        })
        r.raise_for_status()
        # The HTML payload contains raw tabs/newlines, so relax strict JSON.
        data = json.loads(r.text, strict=False).get("data", {})
        max_pages = int(data.get("max_pages", 1) or 1)

        soup = BeautifulSoup(data.get("html", ""), "html.parser")
        for card in soup.select(".mspca-pet-card"):
            link = card.select_one("a.mspca-pet-card-link")
            if not link or not link.get("href"):
                continue
            url = link["href"]
            m = re.search(r"/pets/([a-z0-9]+)/?", url, re.I)
            uid = f"mspca:{m.group(1).lower()}" if m else f"mspca:{url}"

            name_el = card.select_one(".mspca-pet-name")
            loc_el = card.select_one(".mspca-pet-location")
            age_el = card.select_one(".mspca-pet-age")
            img_el = card.select_one(".mspca-pet-card-image")

            pets.append(Pet(
                source=SOURCE, uid=uid,
                name=name_el.get_text(strip=True) if name_el else "Unknown",
                url=url,
                age=age_el.get_text(" ", strip=True) if age_el else "",
                location=loc_el.get_text(" ", strip=True) if loc_el else "",
                photo=_bg_image(img_el.get("style", "")) if img_el else "",
            ))
        page += 1

    return pets


def enrich(session: requests.Session, pet: Pet) -> None:
    """Fetch the detail page to fill in breed and exact weight."""
    r = session.get(pet.url, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    breed_el = soup.select_one(".mspca-pet-breed")
    if breed_el:
        pet.breed = breed_el.get_text(" ", strip=True)

    for item in soup.select(".mspca-stat-item"):
        label = item.select_one(".mspca-stat-label")
        value = item.select_one(".mspca-stat-value")
        if not (label and value):
            continue
        if "weight" in label.get_text(strip=True).lower():
            m = re.search(r"(\d+\.?\d*)", value.get_text())
            if m:
                pet.weight_lb = float(m.group(1))
