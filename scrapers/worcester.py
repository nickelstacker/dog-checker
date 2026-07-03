"""Worcester Animal Rescue League - plain HTML, weight in a data attribute.

Each dog is a `<div class="pp_tile" data-weight="19" ...>` containing the
name, breed, age, sex and a link to the profile page. Best case of the three:
the exact weight is right there in the listing.
"""

from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from models import Pet
from util import TIMEOUT

SOURCE = "Worcester ARL"
URL = "https://worcesterarl.org/dogs-for-adoption/"


def _weight(tile) -> float | None:
    raw = tile.get("data-weight")
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    # Fallback: parse "Weight:</b> 19 lb" out of the inline content.
    m = re.search(r"Weight:.*?(\d+\.?\d*)\s*lb", tile.get_text(" ", strip=True), re.I)
    return float(m.group(1)) if m else None


def scrape(session: requests.Session) -> list[Pet]:
    r = session.get(URL, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    pets: list[Pet] = []
    for tile in soup.select("div.pp_tile"):
        link = tile.find("a", href=re.compile(r"/dogs-for-adoption/pp\d+"))
        if not link:
            continue
        href = link["href"]
        m = re.search(r"/pp(\d+)", href)
        uid = f"worcester:{m.group(1)}" if m else f"worcester:{href}"

        name_el = tile.select_one(".pp_tile_name")
        name = name_el.get_text(strip=True) if name_el else link.get_text(strip=True)

        breed_el = tile.select_one(".ppListItemBreed")
        breed = breed_el.get_text(" ", strip=True) if breed_el else ""

        text = tile.get_text(" ", strip=True)
        age = _field(text, "Age")
        sex = _field(text, "Sex")

        img = tile.select_one("img.pp_hero_image") or tile.find("img")
        photo = img["src"] if img and img.get("src") else ""

        pets.append(Pet(
            source=SOURCE, uid=uid, name=name, url=href, breed=breed,
            age=age, sex=sex, location="Worcester, MA",
            weight_lb=_weight(tile), photo=photo,
        ))
    return pets


def _field(text: str, label: str) -> str:
    m = re.search(rf"{label}:\s*([^\n]+?)(?:\s{{2,}}|Sex:|Weight:|Age:|$)", text, re.I)
    return m.group(1).strip() if m else ""


def enrich(session: requests.Session, pet: Pet) -> None:
    """Weight already present in the listing; nothing more to do."""
    return
