"""Animal Rescue League of Boston, via the 24petconnect platform.

The listing is server-rendered HTML: each dog is a `<div class="gridResult">`
with spans like `text_Name`, `text_Breed`, `text_Age`, `text_Gender`.

Important limitation: 24petconnect publishes **no weight** for ARL Boston -
not in the listing and not on the detail page. So these dogs are matched by a
breed-based size guess (see models.is_match) and always flagged
"weight not listed" in the alert.
"""

from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from models import Pet
from util import TIMEOUT

SOURCE = "ARL Boston"
BASE = "https://24petconnect.com"
URL = f"{BASE}/ARLBostonAdoptablePets?at=DOG&age=A"

# onclick="Details('ARLBostonAdoptablePets', 'BSTN1', 'A300389')"
_DETAILS = re.compile(r"Details\('([^']+)',\s*'([^']+)',\s*'([^']+)'\)")


def _text(card, label: str) -> str:
    el = card.select_one(f"span.text_{label}")
    return el.get_text(" ", strip=True) if el else ""


def scrape(session: requests.Session) -> list[Pet]:
    r = session.get(URL, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    pets: list[Pet] = []
    for card in soup.select("div.gridResult"):
        if _text(card, "Animaltype").lower() not in ("", "dog"):
            continue

        raw_name = _text(card, "Name")  # "PRINCE CHARMING (A300389)"
        m = re.match(r"(.*?)\s*\(([^)]+)\)\s*$", raw_name)
        if m:
            name, animal_id = m.group(1).strip().title(), m.group(2).strip()
        else:
            name, animal_id = raw_name.title(), card.get("id", "").replace("Result_", "")

        url = URL
        onclick = card.get("onclick", "")
        dm = _DETAILS.search(onclick)
        if dm:
            url = f"{BASE}/{dm.group(1)}/Details/{dm.group(2)}/{dm.group(3)}"

        img = card.find("img")
        photo = ""
        if img and img.get("src"):
            src = img["src"]
            photo = src if src.startswith("http") else BASE + src

        pets.append(Pet(
            source=SOURCE, uid=f"arlboston:{animal_id}", name=name, url=url,
            breed=_text(card, "Breed"), age=_text(card, "Age"),
            sex=_text(card, "Gender"),
            location=_text(card, "Locatedat") or "Boston, MA",
            weight_lb=None, photo=photo,
        ))
    return pets


def enrich(session: requests.Session, pet: Pet) -> None:
    """No weight is available for this source; nothing to enrich."""
    return
